from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class Citation:
    source: str
    excerpt: str
    url: str | None = None


@dataclass(frozen=True)
class AgentResponse:
    task_id: UUID
    content: str
    citations: tuple[Citation, ...] = field(default_factory=tuple)
    metadata: dict = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.content.strip()
