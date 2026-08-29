import json
from typing import Any
from uuid import UUID

from redis.asyncio import Redis


class RedisWorkingMemory:
    """Redis-backed working memory. Use for multi-process or distributed deployments."""

    def __init__(self, client: Redis) -> None:
        self._redis = client

    async def get(self, key: str) -> Any | None:
        raw = await self._redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        serialized = json.dumps(value)
        if ttl_seconds is not None:
            await self._redis.setex(key, ttl_seconds, serialized)
        else:
            await self._redis.set(key, serialized)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def clear(self, scope: UUID) -> None:
        pattern = f"{scope}:*"
        keys = await self._redis.keys(pattern)
        if keys:
            await self._redis.delete(*keys)
