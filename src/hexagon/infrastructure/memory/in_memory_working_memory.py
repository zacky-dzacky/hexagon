import asyncio
import time
from typing import Any
from uuid import UUID


class InMemoryWorkingMemory:
    """In-process working memory with optional TTL. Suitable for testing and single-process deployments."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float | None]] = {}  # key -> (value, expires_at)

    def _is_expired(self, expires_at: float | None) -> bool:
        return expires_at is not None and time.monotonic() > expires_at

    async def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if self._is_expired(expires_at):
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expires_at = time.monotonic() + ttl_seconds if ttl_seconds is not None else None
        self._store[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def clear(self, scope: UUID) -> None:
        prefix = str(scope)
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
