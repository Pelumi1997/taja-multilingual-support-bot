from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from taja_bot.config import Settings


@dataclass(frozen=True)
class ParsedGupshupMessage:
    event_type: str
    sender: str | None
    message: str | None
    app_name: str | None


class GupshupAdapter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @staticmethod
    def parse(payload: dict[str, Any]) -> ParsedGupshupMessage:
        event_type = str(payload.get("type", ""))
        app_name = payload.get("app")
        inner = payload.get("payload") or {}
        if event_type == "user-event":
            return ParsedGupshupMessage(
                event_type=event_type,
                sender=inner.get("phone"),
                message="start" if inner.get("type") == "opted-in" else None,
                app_name=app_name,
            )
        sender = (inner.get("sender") or {}).get("phone")
        message = (inner.get("payload") or {}).get("text")
        return ParsedGupshupMessage(
            event_type=event_type,
            sender=str(sender) if sender else None,
            message=str(message).strip() if message else None,
            app_name=app_name,
        )

    @property
    def configured(self) -> bool:
        return all(
            [
                self.settings.gupshup_api_key,
                self.settings.gupshup_app_name,
                self.settings.gupshup_source,
            ]
        )

    async def send_text(self, destination: str, message: str) -> dict[str, Any]:
        if not self.configured:
            raise RuntimeError("Gupshup is not configured")
        payload = {
            "source": self.settings.gupshup_source,
            "channel": "whatsapp",
            "destination": destination,
            "src.name": self.settings.gupshup_app_name,
            "message": message,
        }
        headers = {
            "apikey": str(self.settings.gupshup_api_key),
            "Cache-Control": "no-cache",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(self.settings.gupshup_api_url, data=payload, headers=headers)
            response.raise_for_status()
            return response.json()
