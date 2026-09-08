from __future__ import annotations

import re
from dataclasses import dataclass

from taja_bot.models import EscalationPriority, Intent, LanguageCode


@dataclass(frozen=True)
class SafetyDecision:
    intent: Intent
    escalate: bool
    priority: EscalationPriority
    redacted_text: str
    triggered_rules: tuple[str, ...]


FRAUD_PATTERNS = (
    r"\bfraud\b",
    r"\bscam(?:med)?\b",
    r"\bhack(?:ed)?\b",
    r"\bstolen\b",
    r"unauthori[sz]ed",
    r"not my transaction",
    r"transaction.*not (?:mine|me)",
    r"did not make.*transaction",
    r"unknown transaction",
    r"account.*compromised",
    r"phishing",
    r"zamba",
    r"agh[uụ]gh[oọ]",
    r"jibiti",
)
COMPLAINT_PATTERNS = (
    r"formal complaint",
    r"\bcomplain(?:t|ing)?\b",
    r"unacceptable",
    r"report this",
    r"refund",
    r"money missing",
    r"funds missing",
    r"owo mi sonu",
    r"ego m furu",
)
ACCOUNT_PATTERNS = (
    r"locked out",
    r"cannot log ?in",
    r"can't log ?in",
    r"account blocked",
    r"account suspended",
    r"verification failed",
    r"kyc failed",
    r"login problem",
    r"asusun.*kulle",
    r"ak[aà]ọ?u?nt[uụ].*mechiri",
    r"a?k[oọ]ọl[eẹ].*t[iì]",
)
ADVICE_PATTERNS = (
    r"should i buy",
    r"price prediction",
    r"will bitcoin",
    r"best crypto to buy",
    r"investment advice",
    r"tax advice",
    r"legal advice",
)

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "otp",
        re.compile(
            r"(?i)\b(?:otp|one[- ]?time password|verification code)"
            r"\s*(?:is\s*)?[:=-]?\s*\d{4,8}\b"
        ),
    ),
    ("card_number", re.compile(r"\b(?:\d[ -]*?){13,19}\b")),
    (
        "cvv",
        re.compile(r"(?i)\b(?:cvv|cvc)\s*(?:is\s*)?[:=-]?\s*\d{3,4}\b"),
    ),
    (
        "pin",
        re.compile(r"(?i)\bpin\s*(?:is\s*)?[:=-]?\s*\d{4,8}\b"),
    ),
    (
        "password",
        re.compile(r"(?i)\bpassword\s*(?:is\s*)?[:=-]?\s*\S+"),
    ),
    (
        "wallet_secret",
        re.compile(
            r"(?i)\b(?:seed phrase|recovery phrase|private key)"
            r"\s*(?:is\s*)?[:=-]?\s*[^,.!?;]{4,160}"
        ),
    ),
)


class SafetyService:
    """Classify high-risk support messages and redact secrets before logging."""

    @staticmethod
    def _matches(patterns: tuple[str, ...], text: str) -> bool:
        return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)

    @staticmethod
    def redact(text: str) -> tuple[str, tuple[str, ...]]:
        redacted = text
        triggered: list[str] = []
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(redacted):
                triggered.append(name)
                redacted = pattern.sub(f"[{name.upper()} REDACTED]", redacted)
        return redacted, tuple(triggered)

    def classify(self, message: str, language: LanguageCode) -> SafetyDecision:
        del language  # Reserved for language-specific policy expansion.
        redacted, secret_rules = self.redact(message)

        if secret_rules:
            return SafetyDecision(
                intent=Intent.FRAUD_SECURITY,
                escalate=True,
                priority=EscalationPriority.CRITICAL,
                redacted_text=redacted,
                triggered_rules=secret_rules,
            )
        if self._matches(FRAUD_PATTERNS, redacted):
            return SafetyDecision(
                intent=Intent.FRAUD_SECURITY,
                escalate=True,
                priority=EscalationPriority.CRITICAL,
                redacted_text=redacted,
                triggered_rules=("fraud_security",),
            )
        if self._matches(COMPLAINT_PATTERNS, redacted):
            return SafetyDecision(
                intent=Intent.COMPLAINT,
                escalate=True,
                priority=EscalationPriority.HIGH,
                redacted_text=redacted,
                triggered_rules=("complaint",),
            )
        if self._matches(ACCOUNT_PATTERNS, redacted):
            return SafetyDecision(
                intent=Intent.ACCOUNT_ACCESS,
                escalate=True,
                priority=EscalationPriority.HIGH,
                redacted_text=redacted,
                triggered_rules=("account_access",),
            )
        if self._matches(ADVICE_PATTERNS, redacted):
            return SafetyDecision(
                intent=Intent.RESTRICTED_ADVICE,
                escalate=False,
                priority=EscalationPriority.NONE,
                redacted_text=redacted,
                triggered_rules=("restricted_advice",),
            )
        return SafetyDecision(
            intent=Intent.ROUTINE,
            escalate=False,
            priority=EscalationPriority.NONE,
            redacted_text=redacted,
            triggered_rules=(),
        )
