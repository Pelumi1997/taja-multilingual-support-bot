from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime

from taja_bot.config import Settings
from taja_bot.models import (
    ChatRequest,
    ChatResponse,
    EscalationPriority,
    Intent,
    LanguageCode,
)
from taja_bot.services.faq import FaqService
from taja_bot.services.generation import AnswerGenerator
from taja_bot.services.language import LanguageService
from taja_bot.services.safety import SafetyDecision, SafetyService
from taja_bot.services.session import SessionStore


MENU_COMMANDS = {
    "0", "menu", "help", "faq", "faqs", "start", "hello", "hi", "hey",
    "how far", "bawo", "yaya", "kedu", "ndewo", "sannu",
}
LANGUAGE_COMMANDS = {
    "language", "change language", "select language", "ede", "harshe", "asusu", "language menu",
}


class ChatService:
    def __init__(
        self,
        *,
        settings: Settings,
        faq_service: FaqService,
        language_service: LanguageService,
        safety_service: SafetyService,
        session_store: SessionStore,
        answer_generator: AnswerGenerator,
    ) -> None:
        self.settings = settings
        self.faqs = faq_service
        self.languages = language_service
        self.safety = safety_service
        self.sessions = session_store
        self.generator = answer_generator

    @staticmethod
    def _normalise_command(message: str) -> str:
        return re.sub(r"\s+", " ", message.casefold().strip())

    def _case_reference(self, session_id: str) -> str:
        timestamp = datetime.now(UTC).strftime("%Y%m%d")
        digest = hmac.new(
            self.settings.pseudonymisation_salt.encode("utf-8"),
            f"{session_id}:{secrets.token_hex(8)}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()[:8].upper()
        return f"TJA-{timestamp}-{digest}"

    def _localised_safety_reply(self, decision: SafetyDecision, language: LanguageCode) -> str:
        key = {
            Intent.FRAUD_SECURITY: "fraud_reply",
            Intent.COMPLAINT: "complaint_reply",
            Intent.ACCOUNT_ACCESS: "account_reply",
            Intent.RESTRICTED_ADVICE: "advice_reply",
        }.get(decision.intent, "fallback_reply")
        return self.faqs.text(key, language).format(support_url=self.settings.support_url)

    async def process(self, request: ChatRequest) -> ChatResponse:
        stored_language = await self.sessions.get_language(request.session_id)
        selected_language = (
            self.languages.parse_selection(
                request.message,
                allow_menu_numbers=stored_language is None,
            )
            if request.language is None
            else None
        )
        language = self.languages.resolve(
            explicit=request.language,
            message=request.message,
            stored=stored_language,
        )

        command = self._normalise_command(request.message)
        if command in LANGUAGE_COMMANDS:
            await self.sessions.clear(request.session_id)
            return ChatResponse(
                session_id=request.session_id,
                language=LanguageCode.ENGLISH,
                reply=self.faqs.language_menu(),
                intent=Intent.MENU,
                confidence=1.0,
            )

        if selected_language is not None and request.language is None:
            await self.sessions.set_language(request.session_id, selected_language)
            return ChatResponse(
                session_id=request.session_id,
                language=selected_language,
                reply=self.faqs.text("language_confirmed", selected_language) + "\n\n" + self.faqs.menu(selected_language),
                intent=Intent.MENU,
                confidence=1.0,
            )

        if stored_language is None and request.language is None and command in MENU_COMMANDS:
            return ChatResponse(
                session_id=request.session_id,
                language=LanguageCode.ENGLISH,
                reply=self.faqs.language_menu(),
                intent=Intent.MENU,
                confidence=1.0,
            )

        await self.sessions.set_language(request.session_id, language)

        if command in MENU_COMMANDS:
            return ChatResponse(
                session_id=request.session_id,
                language=language,
                reply=self.faqs.menu(language),
                intent=Intent.MENU,
                confidence=1.0,
            )

        decision = self.safety.classify(request.message, language)
        if decision.intent in {
            Intent.FRAUD_SECURITY,
            Intent.COMPLAINT,
            Intent.ACCOUNT_ACCESS,
            Intent.RESTRICTED_ADVICE,
        }:
            requires_human = decision.escalate
            reference = self._case_reference(request.session_id) if requires_human else None
            reply = self._localised_safety_reply(decision, language)
            if reference:
                reply = f"{reply} {self.faqs.text('case_reference', language).format(case_reference=reference)}"
            return ChatResponse(
                session_id=request.session_id,
                language=language,
                reply=reply,
                intent=decision.intent,
                confidence=1.0,
                requires_human=requires_human,
                escalation_priority=decision.priority,
                case_reference=reference,
                redacted_input=decision.redacted_text if decision.redacted_text != request.message else None,
            )

        match = self.faqs.match(request.message, language)
        if match.score < self.settings.min_match_score:
            reference = self._case_reference(request.session_id)
            return ChatResponse(
                session_id=request.session_id,
                language=language,
                reply=(
                    self.faqs.text("fallback_reply", language).format(support_url=self.settings.support_url)
                    + " "
                    + self.faqs.text("case_reference", language).format(case_reference=reference)
                ),
                intent=Intent.UNSUPPORTED,
                confidence=match.score,
                requires_human=True,
                escalation_priority=EscalationPriority.NORMAL,
                case_reference=reference,
            )

        source_references = self.faqs.sources(match.faq)
        generated = await self.generator.generate(
            question=decision.redacted_text,
            language=language,
            faq_id=match.faq["id"],
            approved_answer=self.faqs.answer(match.faq, language),
            source_urls=[source.url for source in source_references],
        )
        return ChatResponse(
            session_id=request.session_id,
            language=language,
            reply=generated.text,
            intent=Intent.ROUTINE,
            matched_faq_id=match.faq["id"],
            confidence=match.score,
            sources=source_references,
            answer_mode=generated.mode,
            generation_fallback=generated.used_fallback,
        )
