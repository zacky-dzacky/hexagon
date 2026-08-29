import uuid
from dataclasses import dataclass, field

from hexagon.domain.entities.chunk import Chunk


@dataclass
class _Document:
    id: str
    content: str
    source: str
    metadata: dict = field(default_factory=dict)


class InMemoryRetrievalAdapter:
    """In-process retrieval using keyword-overlap scoring.

    Swap for ChromaDB, Pinecone, or pgvector in production to get real embedding similarity.
    """

    def __init__(self) -> None:
        self._docs: dict[str, _Document] = {}

    async def retrieve(self, query: str, top_k: int = 5) -> list[Chunk]:
        query_tokens = set(query.lower().split())
        scored: list[tuple[float, _Document]] = []
        for doc in self._docs.values():
            doc_tokens = set(doc.content.lower().split())
            union = doc_tokens | query_tokens
            if not union:
                continue
            score = len(query_tokens & doc_tokens) / len(union)  # Jaccard
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            Chunk(content=doc.content, source=doc.source, score=score, metadata=doc.metadata)
            for score, doc in scored[:top_k]
        ]

    async def index(self, content: str, source: str, metadata: dict | None = None) -> str:
        doc_id = str(uuid.uuid4())
        self._docs[doc_id] = _Document(id=doc_id, content=content, source=source, metadata=metadata or {})
        return doc_id

    async def delete(self, document_id: str) -> None:
        self._docs.pop(document_id, None)
