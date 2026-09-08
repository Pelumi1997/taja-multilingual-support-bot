from taja_bot.models import EscalationPriority, Intent, LanguageCode
from taja_bot.services.safety import SafetyService


def test_fraud_is_critical() -> None:
    decision = SafetyService().classify("I can see an unauthorised transaction", LanguageCode.ENGLISH)
    assert decision.intent == Intent.FRAUD_SECURITY
    assert decision.escalate is True
    assert decision.priority == EscalationPriority.CRITICAL


def test_otp_is_redacted() -> None:
    decision = SafetyService().classify("My OTP is 123456", LanguageCode.ENGLISH)
    assert "123456" not in decision.redacted_text
    assert "OTP REDACTED" in decision.redacted_text
    assert decision.priority == EscalationPriority.CRITICAL


def test_security_question_is_not_a_fraud_report() -> None:
    decision = SafetyService().classify("Is Taja secure?", LanguageCode.ENGLISH)
    assert decision.intent == Intent.ROUTINE
