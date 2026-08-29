from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Protocol, runtime_checkable

from hexagon.domain.entities.message import Message


@dataclass(frozen=True)
class ToolSchema:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema object


@dataclass(frozen=True)
class LLMResponse:
    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = "end_turn"


@runtime_checkable
class LanguageModelPort(Protocol):
    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolSchema] | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse: ...

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema] | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]: ...
