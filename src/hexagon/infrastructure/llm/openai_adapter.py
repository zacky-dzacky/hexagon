import json
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from hexagon.domain.entities.message import Message
from hexagon.domain.ports.outbound.language_model import LLMResponse, ToolSchema


def _to_openai_message(msg: Message) -> dict[str, Any]:
    return {"role": msg.role.value, "content": msg.content}


def _to_openai_tool(schema: ToolSchema) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": schema.name,
            "description": schema.description,
            "parameters": schema.parameters,
        },
    }


class OpenAIAdapter:
    def __init__(self, model: str = "gpt-4o", api_key: str | None = None) -> None:
        self._model = model
        self._api_key = api_key
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self._api_key)
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
            "messages": [_to_openai_message(m) for m in messages],
        }
        if tools:
            kwargs["tools"] = [_to_openai_tool(t) for t in tools]

        response = await self._get_client().chat.completions.create(**kwargs)
        choice = response.choices[0]
        msg = choice.message

        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                })

        return LLMResponse(
            content=msg.content or "",
            tool_calls=tool_calls,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            stop_reason=choice.finish_reason or "stop",
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
            "messages": [_to_openai_message(m) for m in messages],
            "stream": True,
        }
        if tools:
            kwargs["tools"] = [_to_openai_tool(t) for t in tools]

        async for chunk in await self._get_client().chat.completions.create(**kwargs):
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
