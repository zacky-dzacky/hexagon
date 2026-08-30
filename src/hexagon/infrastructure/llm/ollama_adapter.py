from collections.abc import AsyncIterator
from typing import Any

from ollama import AsyncClient
from ollama._types import Message as OllamaMessage

from hexagon.domain.entities.message import Message
from hexagon.domain.ports.outbound.language_model import LLMResponse, ToolSchema


def _to_ollama_message(msg: Message) -> OllamaMessage:
    return OllamaMessage(role=msg.role.value, content=msg.content)


def _to_ollama_tool(schema: ToolSchema) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": schema.name,
            "description": schema.description,
            "parameters": schema.parameters,
        },
    }


class OllamaAdapter:
    """LanguageModelPort adapter for locally-running Ollama models.

    Defaults to localhost:11434. Override host for remote or containerized instances.
    """

    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434") -> None:
        self._model = model
        self._client = AsyncClient(host=host)

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolSchema] | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": [_to_ollama_message(m) for m in messages],
            "options": {"num_predict": max_tokens},
        }
        if tools:
            kwargs["tools"] = [_to_ollama_tool(t) for t in tools]

        response = await self._client.chat(**kwargs)
        msg = response.message

        tool_calls: list[dict[str, Any]] = []
        if msg.tool_calls:
            for i, tc in enumerate(msg.tool_calls):
                tool_calls.append({
                    "id": f"call_{i}",
                    "name": tc.function.name,
                    "arguments": dict(tc.function.arguments or {}),
                })

        return LLMResponse(
            content=msg.content or "",
            tool_calls=tool_calls,
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema] | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": [_to_ollama_message(m) for m in messages],
            "stream": True,
            "options": {"num_predict": max_tokens},
        }
        if tools:
            kwargs["tools"] = [_to_ollama_tool(t) for t in tools]

        async for chunk in await self._client.chat(**kwargs):
            content = chunk.message.content
            if content:
                yield content
