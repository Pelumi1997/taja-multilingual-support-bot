import pytest

from taja_bot.config import Settings
from taja_bot.models import LanguageCode
from taja_bot.services.generation import (
    DeterministicAnswerGenerator,
    OpenAIRagAnswerGenerator,
    build_answer_generator,
)


@pytest.mark.asyncio
async def test_deterministic_generator_returns_approved_answer() -> None:
    generator = DeterministicAnswerGenerator()
    result = await generator.generate(
        question="How fast?",
        language=LanguageCode.ENGLISH,
        faq_id="transfer-speed",
        approved_answer="Within minutes.",
        source_urls=["https://example.com"],
    )
    assert result.text == "Within minutes."
    assert result.mode == "deterministic"
    assert result.used_fallback is False


def test_responses_output_parser_supports_both_shapes() -> None:
    assert OpenAIRagAnswerGenerator.extract_output_text({"output_text": "Direct"}) == "Direct"
    nested = {
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": "Nested"}],
            }
        ]
    }
    assert OpenAIRagAnswerGenerator.extract_output_text(nested) == "Nested"
    assert OpenAIRagAnswerGenerator.extract_output_text({"output": []}) == ""


def test_openai_mode_requires_api_key() -> None:
    settings = Settings(environment="test", answer_mode="openai", openai_api_key=None)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        build_answer_generator(settings)
