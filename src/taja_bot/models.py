from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class LanguageCode(StrEnum):
    ENGLISH = "en"
    PIDGIN = "pcm"
    HAUSA = "ha"
    IGBO = "ig"
    YORUBA = "yo"


class Intent(StrEnum):
    ROUTINE = "routine"
    COMPLAINT = "complaint"
    FRAUD_SECURITY = "fraud_security"
    ACCOUNT_ACCESS = "account_access"
    RESTRICTED_ADVICE = "restricted_advice"
    UNSUPPORTED = "unsupported"
    MENU = "menu"


class EscalationPriority(StrEnum):
    NONE = "none"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class SourceReference(BaseModel):
    title: str
    url: str
    last_verified: str | None = None


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=2000)
    language: LanguageCode | None = None
    channel: str = Field(default="api", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("session_id", "message", "channel")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class ChatResponse(BaseModel):
    session_id: str
    language: LanguageCode
    reply: str
    intent: Intent
    matched_faq_id: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    requires_human: bool = False
    escalation_priority: EscalationPriority = EscalationPriority.NONE
    case_reference: str | None = None
    sources: list[SourceReference] = Field(default_factory=list)
    answer_mode: str = "deterministic"
    generation_fallback: bool = False
    redacted_input: str | None = None


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    knowledge_base_entries: int


class LanguageOption(BaseModel):
    code: LanguageCode
    name: str
    native_name: str
    menu_number: int


class PublicFaq(BaseModel):
    id: str
    category: str
    question: str
    answer: str
    sources: list[SourceReference]


class GupshupDelivery(BaseModel):
    attempted: bool
    delivered: bool
    mode: str
    provider_response: dict[str, Any] | None = None


class GupshupWebhookResponse(BaseModel):
    accepted: bool
    chatbot: ChatResponse | None = None
    delivery: GupshupDelivery | None = None
    detail: str | None = None
