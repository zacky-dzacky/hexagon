import uuid
from typing import Any


class InMemoryEpisodicMemory:
    """In-process episodic memory with keyword-overlap search.

    Production deployments should swap this for a vector-DB-backed adapter
    (Pinecone, ChromaDB, etc.) that uses embedding similarity instead.
    """

    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}

    async def store(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        memory_id = str(uuid.uuid4())
        self._records[memory_id] = {"id": memory_id, "content": content, "metadata": metadata or {}}
        return memory_id

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_tokens = set(query.lower().split())
        scored = []
        for record in self._records.values():
            doc_tokens = set(record["content"].lower().split())
            overlap = len(query_tokens & doc_tokens)
            if overlap > 0:
                scored.append((overlap, record))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:top_k]]

    async def delete(self, memory_id: str) -> None:
        self._records.pop(memory_id, None)
