from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class ToolResult:
    tool_call_id: str
    name: str
    content: Any
    is_error: bool = False


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema


@runtime_checkable
class ToolPort(Protocol):
    """A single executable tool the agent can invoke."""

    @property
    def definition(self) -> ToolDefinition: ...

    async def execute(self, tool_call_id: str, arguments: dict[str, Any]) -> ToolResult: ...


@runtime_checkable
class ToolRegistryPort(Protocol):
    """Provides the agent with a collection of available tools."""

    def get_tools(self) -> list[ToolPort]: ...

    def get_definitions(self) -> list[ToolDefinition]: ...

    def get(self, name: str) -> ToolPort | None: ...
