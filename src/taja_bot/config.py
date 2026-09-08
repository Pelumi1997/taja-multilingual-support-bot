from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or a .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Taja Multilingual Support Bot"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    default_language: str = "en"
    min_match_score: float = Field(default=0.52, ge=0.0, le=1.0)
    answer_mode: Literal["deterministic", "openai"] = "deterministic"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-luna"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_timeout_seconds: float = Field(default=20.0, gt=0.0, le=120.0)
    session_backend: Literal["memory", "redis"] = "memory"
    session_ttl_seconds: int = Field(default=604800, ge=60)
    redis_url: str | None = None

    webhook_secret: str | None = None
    pseudonymisation_salt: str = "change-this-in-production"

    gupshup_api_key: str | None = None
    gupshup_app_name: str | None = None
    gupshup_source: str | None = None
    gupshup_api_url: str = "https://api.gupshup.io/sm/api/v1/msg"

    support_url: str = "https://www.tajahq.com/contact"
    allowed_origins: Annotated[list[str], NoDecode] = ["http://localhost:8000"]

    faq_data_path: Path = Path(__file__).resolve().parent / "data" / "faqs.json"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("default_language")
    @classmethod
    def validate_default_language(cls, value: str) -> str:
        supported = {"en", "pcm", "ha", "ig", "yo"}
        normalised = value.strip().lower()
        if normalised not in supported:
            raise ValueError(f"default_language must be one of {sorted(supported)}")
        return normalised


@lru_cache
def get_settings() -> Settings:
    return Settings()
