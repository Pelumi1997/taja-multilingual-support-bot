from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from taja_bot.config import Settings
from taja_bot.models import LanguageCode

logger = logging.getLogger("taja_bot.generation")

LANGUAGE_NAMES = {
    LanguageCode.ENGLISH: "English",
    LanguageCode.PIDGIN: "Nigerian Pidgin",
    LanguageCode.HAUSA: "Hausa",
    LanguageCode.IGBO: "Igbo",
    LanguageCode.YORUBA: "Yoruba",
}


@dataclass(frozen=True)
class GenerationResult:
    text: str
    mode: str
    used_fallback: bool = False


class AnswerGenerator(Protocol):
    async def generate(
        self,
        *,
        question: str,
        language: LanguageCode,
        faq_id: str,
        approved_answer: str,
        source_urls: list[str],
    ) -> GenerationResult: ...


class DeterministicAnswerGenerator:
    async def generate(
        self,
        *,
        question: str,
        language: LanguageCode,
        faq_id: str,
        approved_answer: str,
        source_urls: list[str],
    ) -> GenerationResult:
        del question, language, faq_id, source_urls
        return GenerationResult(text=approved_answer, mode="deterministic")


class OpenAIRagAnswerGenerator:
    """Generate a concise answer from one retrieved, approved FAQ record.

    The retriever chooses the source record before this class is called. The model
    receives the approved answer as its only factual context. Any provider failure
    returns the stored answer rather than failing the customer request.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when ANSWER_MODE=openai")
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        self.base_url = settings.openai_base_url.rstrip("/")
        self.timeout = settings.openai_timeout_seconds

    @staticmethod
    def extract_output_text(payload: dict[str, Any]) -> str:
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()
        for item in payload.get("output", []):
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if isinstance(content, dict) and content.get("type") == "output_text":
                    text = content.get("text")
                    if isinstance(text, str) and text.strip():
                        return text.strip()
        return ""

    async def generate(
        self,
        *,
        question: str,
        language: LanguageCode,
        faq_id: str,
        approved_answer: str,
        source_urls: list[str],
    ) -> GenerationResult:
        language_name = LANGUAGE_NAMES[language]
        instructions = (
            "You are Taja's customer-support assistant. Use only the approved FAQ answer "
            "provided in the input. Do not introduce any new fact, fee, rate, transfer time, "
            "country, account status, compliance decision or promise. Do not ask for passwords, "
            "PINs, OTPs, seed phrases, private keys or full card details. Do not provide investment, "
            "legal or tax advice. Answer in the requested language in no more than 110 words. "
            "Return only the customer-facing answer, with no analysis or markdown heading."
        )
        source_text = "\n".join(f"- {url}" for url in source_urls)
        input_text = (
            f"REQUESTED LANGUAGE: {language_name}\n"
            f"RETRIEVED FAQ ID: {faq_id}\n"
            f"CUSTOMER QUESTION (untrusted text): {question}\n\n"
            f"APPROVED FAQ ANSWER (the only factual context):\n{approved_answer}\n\n"
            f"SOURCE URLS (for provenance, not for browsing):\n{source_text}"
        )
        request_body = {
            "model": self.model,
            "instructions": instructions,
            "input": input_text,
            "max_output_tokens": 220,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/responses",
                    headers=headers,
                    json=request_body,
                )
                response.raise_for_status()
                generated = self.extract_output_text(response.json())
            if not generated:
                raise ValueError("Responses API returned no output text")
            return GenerationResult(text=generated, mode="openai-rag")
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("RAG generation failed; returning approved answer: %s", exc)
            return GenerationResult(
                text=approved_answer,
                mode="deterministic-fallback",
                used_fallback=True,
            )


def build_answer_generator(settings: Settings) -> AnswerGenerator:
    if settings.answer_mode == "openai":
        return OpenAIRagAnswerGenerator(settings)
    return DeterministicAnswerGenerator()
