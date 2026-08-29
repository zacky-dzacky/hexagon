from collections.abc import AsyncIterator
from collections import deque

from hexagon.domain.entities.message import Message
from hexagon.domain.ports.outbound.language_model import LLMResponse, ToolSchema


class MockLLMAdapter:
    """Deterministic LLM adapter for testing — returns canned responses in order."""

    def __init__(self, responses: list[LLMResponse] | None = None) -> None:
        self._queue: deque[LLMResponse] = deque(responses or [])
        self._default = LLMResponse(content="mock response")
        self.calls: list[tuple[list[Message], list[ToolSchema] | None]] = []

    def enqueue(self, response: LLMResponse) -> None:
        self._queue.append(response)

    def _next(self, messages: list[Message], tools: list[ToolSchema] | None) -> LLMResponse:
        self.calls.append((messages, tools))
        return self._queue.popleft() if self._queue else self._default

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolSchema] | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        return self._next(messages, tools)

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema] | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        response = self._next(messages, tools)
        for word in response.content.split():
            yield word + " "
