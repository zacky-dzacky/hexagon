from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Role(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class Message:
    role: Role
    content: str
    tool_calls: tuple[ToolCall, ...] = field(default_factory=tuple)
    tool_call_id: str | None = None

    @staticmethod
    def system(content: str) -> "Message":
        return Message(role=Role.SYSTEM, content=content)

    @staticmethod
    def user(content: str) -> "Message":
        return Message(role=Role.USER, content=content)

    @staticmethod
    def assistant(content: str, tool_calls: list[ToolCall] | None = None) -> "Message":
        return Message(role=Role.ASSISTANT, content=content, tool_calls=tuple(tool_calls or []))
