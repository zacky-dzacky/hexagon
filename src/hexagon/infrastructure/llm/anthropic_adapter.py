from collections.abc import AsyncIterator
from typing import Any

import anthropic

from hexagon.domain.entities.message import Message, Role
from hexagon.domain.ports.outbound.language_model import LLMResponse, ToolSchema


def _to_anthropic_tool(schema: ToolSchema) -> dict[str, Any]:
    return {
        "name": schema.name,
        "description": schema.description,
        "input_schema": schema.parameters,
    }


def _to_anthropic_messages(messages: list[Message]) -> list[dict[str, Any]]:
    return [
        {"role": msg.role.value, "content": msg.content}
        for msg in messages
        if msg.role != Role.SYSTEM
    ]


def _extract_system(messages: list[Message]) -> str | None:
    for msg in messages:
        if msg.role == Role.SYSTEM:
            return msg.content
    return None


class AnthropicAdapter:
    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str | None = None) -> None:
        self._model = model
        self._api_key = api_key
        self._client: anthropic.AsyncAnthropic | None = None

    def _get_client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
        return self._client

    async def complete(
        self,
        messages: list[Message],
        tools: list[ToolSchema] | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": _to_anthropic_messages(messages),
        }
        system = _extract_system(messages)
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [_to_anthropic_tool(t) for t in tools]

        response = await self._get_client().messages.create(**kwargs)

        content = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input,
                })

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            stop_reason=response.stop_reason or "end_turn",
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolSchema] | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": _to_anthropic_messages(messages),
        }
        system = _extract_system(messages)
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [_to_anthropic_tool(t) for t in tools]

        async with self._get_client().messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text
