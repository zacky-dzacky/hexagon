from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from hexagon.domain.entities.agent_response import AgentResponse
from hexagon.domain.entities.task import Task


@dataclass(frozen=True)
class SubAgentRequest:
    task: Task
    context: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class SubAgentPort(Protocol):
    """Sends a task to a specialized sub-agent and awaits its response.

    Each sub-agent is its own hexagon; this port abstracts the transport
    (in-process, HTTP, A2A protocol, MCP, etc.).
    """

    @property
    def agent_id(self) -> str: ...

    async def delegate(self, request: SubAgentRequest) -> AgentResponse: ...

    async def health(self) -> bool: ...
