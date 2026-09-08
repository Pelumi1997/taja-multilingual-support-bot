from __future__ import annotations

from pathlib import Path

import pytest

from taja_bot.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment="test",
        session_backend="memory",
        min_match_score=0.52,
        faq_data_path=Path(__file__).resolve().parents[1] / "src" / "taja_bot" / "data" / "faqs.json",
        pseudonymisation_salt="test-only-salt",
        allowed_origins=["http://testserver"],
    )
