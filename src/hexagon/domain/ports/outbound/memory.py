from typing import Any, Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class WorkingMemoryPort(Protocol):
    """Short-term memory scoped to a single agent execution."""

    async def get(self, key: str) -> Any | None: ...

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None: ...

    async def delete(self, key: str) -> None: ...

    async def clear(self, scope: UUID) -> None: ...


@runtime_checkable
class EpisodicMemoryPort(Protocol):
    """Long-term memory: stores and retrieves past interactions semantically."""

    async def store(self, content: str, metadata: dict[str, Any] | None = None) -> str: ...

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]: ...

    async def delete(self, memory_id: str) -> None: ...
