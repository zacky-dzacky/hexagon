from dataclasses import dataclass, field


@dataclass(frozen=True)
class Chunk:
    content: str
    source: str
    score: float = 0.0
    metadata: dict = field(default_factory=dict)
