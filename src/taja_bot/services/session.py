from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from taja_bot.models import LanguageCode


class SessionStore(ABC):
    @abstractmethod
    async def get_language(self, session_id: str) -> LanguageCode | None:
        raise NotImplementedError

    @abstractmethod
    async def set_language(self, session_id: str, language: LanguageCode) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear(self, session_id: str) -> None:
        raise NotImplementedError


@dataclass
class _MemoryValue:
    language: LanguageCode
    expires_at: float


class MemorySessionStore(SessionStore):
    def __init__(self, ttl_seconds: int = 604800) -> None:
        self._ttl = ttl_seconds
        self._values: dict[str, _MemoryValue] = {}
        self._lock = asyncio.Lock()

    async def get_language(self, session_id: str) -> LanguageCode | None:
        async with self._lock:
            value = self._values.get(session_id)
            if value is None:
                return None
            if value.expires_at <= time.time():
                self._values.pop(session_id, None)
                return None
            return value.language

    async def set_language(self, session_id: str, language: LanguageCode) -> None:
        async with self._lock:
            self._values[session_id] = _MemoryValue(
                language=language,
                expires_at=time.time() + self._ttl,
            )

    async def clear(self, session_id: str) -> None:
        async with self._lock:
            self._values.pop(session_id, None)


class RedisSessionStore(SessionStore):
    def __init__(self, redis_url: str, ttl_seconds: int = 604800) -> None:
        try:
            from redis.asyncio import Redis
        except ImportError as exc:  # pragma: no cover - exercised only in Redis deployments.
            raise RuntimeError("Install the 'redis' extra to use RedisSessionStore") from exc
        self._redis = Redis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl_seconds

    @staticmethod
    def _key(session_id: str) -> str:
        return f"taja:session:{session_id}:language"

    async def get_language(self, session_id: str) -> LanguageCode | None:
        value = await self._redis.get(self._key(session_id))
        if value is None:
            return None
        try:
            return LanguageCode(value)
        except ValueError:
            await self.clear(session_id)
            return None

    async def set_language(self, session_id: str, language: LanguageCode) -> None:
        await self._redis.set(self._key(session_id), language.value, ex=self._ttl)

    async def clear(self, session_id: str) -> None:
        await self._redis.delete(self._key(session_id))


def build_session_store(*, backend: str, redis_url: str | None, ttl_seconds: int) -> SessionStore:
    if backend == "redis":
        if not redis_url:
            raise ValueError("REDIS_URL is required when SESSION_BACKEND=redis")
        return RedisSessionStore(redis_url, ttl_seconds)
    return MemorySessionStore(ttl_seconds)
