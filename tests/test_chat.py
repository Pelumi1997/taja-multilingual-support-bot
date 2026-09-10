import pytest

from taja_bot.models import ChatRequest, EscalationPriority, Intent, LanguageCode
from taja_bot.services.chat import ChatService
from taja_bot.services.faq import FaqService
from taja_bot.services.generation import DeterministicAnswerGenerator
from taja_bot.services.language import LanguageService
from taja_bot.services.safety import SafetyService
from taja_bot.services.session import MemorySessionStore


@pytest.fixture
def chat_service(settings) -> ChatService:
    return ChatService(
        settings=settings,
        faq_service=FaqService(settings.faq_data_path),
        language_service=LanguageService(),
        safety_service=SafetyService(),
        session_store=MemorySessionStore(),
        answer_generator=DeterministicAnswerGenerator(),
    )


@pytest.mark.asyncio
async def test_first_hello_returns_language_menu(chat_service: ChatService) -> None:
    response = await chat_service.process(ChatRequest(session_id="one", message="hello"))
    assert response.intent == Intent.MENU
    assert "1. English" in response.reply


@pytest.mark.asyncio
async def test_language_selection_persists(chat_service: ChatService) -> None:
    selected = await chat_service.process(ChatRequest(session_id="two", message="4"))
    assert selected.language == LanguageCode.PIDGIN
    answer = await chat_service.process(ChatRequest(session_id="two", message="How long transfer go take?"))
    assert answer.matched_faq_id == "transfer-speed"
    assert answer.language == LanguageCode.PIDGIN


@pytest.mark.asyncio
async def test_fraud_creates_case_reference(chat_service: ChatService) -> None:
    response = await chat_service.process(
        ChatRequest(session_id="three", message="I see a transaction that is not mine", language="en")
    )
    assert response.intent == Intent.FRAUD_SECURITY
    assert response.requires_human is True
    assert response.escalation_priority == EscalationPriority.CRITICAL
    assert response.case_reference and response.case_reference.startswith("TJA-")


@pytest.mark.asyncio
async def test_unknown_question_routes_to_human(chat_service: ChatService) -> None:
    response = await chat_service.process(
        ChatRequest(session_id="four", message="Can Taja book a hotel in Abuja?", language="en")
    )
    assert response.intent == Intent.UNSUPPORTED
    assert response.requires_human is True

@pytest.mark.asyncio
async def test_faq_number_after_language_selection_does_not_change_language(chat_service: ChatService) -> None:
    await chat_service.process(ChatRequest(session_id="five", message="4"))
    response = await chat_service.process(ChatRequest(session_id="five", message="3"))
    assert response.language == LanguageCode.PIDGIN
    assert response.matched_faq_id == "crypto-to-cash"


@pytest.mark.asyncio
async def test_restricted_advice_is_declined_without_fake_ticket(chat_service: ChatService) -> None:
    response = await chat_service.process(
        ChatRequest(session_id="six", message="Should I buy bitcoin today?", language="en")
    )
    assert response.intent == Intent.RESTRICTED_ADVICE
    assert response.requires_human is False
    assert response.case_reference is None

@pytest.mark.asyncio
async def test_natural_language_switching_across_session(chat_service: ChatService) -> None:
    session_id = "seven"

    # Start in Nigerian Pidgin
    response = await chat_service.process(
        ChatRequest(session_id=session_id, message="4")
    )
    assert response.language == LanguageCode.PIDGIN

    # Natural-language switch to Igbo
    response = await chat_service.process(
        ChatRequest(session_id=session_id, message="can I switch to Igbo?")
    )
    assert response.language == LanguageCode.IGBO
    assert response.intent == Intent.MENU

    # Natural-language switch to Yoruba
    response = await chat_service.process(
        ChatRequest(session_id=session_id, message="can I switch to Yoruba?")
    )
    assert response.language == LanguageCode.YORUBA
    assert response.intent == Intent.MENU

    # Natural-language switch back to English
    response = await chat_service.process(
        ChatRequest(session_id=session_id, message="can I switch to English?")
    )
    assert response.language == LanguageCode.ENGLISH
    assert response.intent == Intent.MENU

    # Confirm the final language persists for a normal FAQ question
    response = await chat_service.process(
        ChatRequest(session_id=session_id, message="How long does a transfer take?")
    )
    assert response.language == LanguageCode.ENGLISH
    assert response.matched_faq_id == "transfer-speed"
