from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis

SESSION_PREFIX = "bff:session:"


class SessionStore:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def _key(self, session_id: str) -> str:
        return f"{SESSION_PREFIX}{session_id}"

    async def save(self, session_id: str, data: dict[str, Any], ttl_seconds: int) -> None:
        await self._redis.set(self._key(session_id), json.dumps(data), ex=ttl_seconds)

    async def get(self, session_id: str) -> dict[str, Any] | None:
        payload = await self._redis.get(self._key(session_id))
        if not payload:
            return None
        return json.loads(payload)

    async def delete(self, session_id: str) -> None:
        await self._redis.delete(self._key(session_id))
