from typing import Protocol, runtime_checkable

from hexagon.domain.entities.chunk import Chunk


@runtime_checkable
class KnowledgeRetrievalPort(Protocol):
    """Retrieves relevant knowledge chunks for a given query (RAG)."""

    async def retrieve(self, query: str, top_k: int = 5) -> list[Chunk]: ...

    async def index(self, content: str, source: str, metadata: dict | None = None) -> str: ...

    async def delete(self, document_id: str) -> None: ...
