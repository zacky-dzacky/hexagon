from typing import AsyncIterator, Protocol, runtime_checkable

from hexagon.domain.entities.agent_response import AgentResponse
from hexagon.domain.entities.task import Task


@runtime_checkable
class TaskHandlerPort(Protocol):
    """Primary port: the entry point for driving the agent with a task.

    Inbound adapters (API, CLI, MCP server) call this — they never touch
    the application or infrastructure layers directly.
    """

    async def handle(self, task: Task) -> AgentResponse: ...

    async def stream(self, task: Task) -> AsyncIterator[str]: ...
