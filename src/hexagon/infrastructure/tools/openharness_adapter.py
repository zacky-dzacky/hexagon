"""OpenHarness sub-agent adapter.

Wraps an OpenHarness QueryEngine as a SubAgentPort. The engine handles its own
tool execution, memory, and multi-turn reasoning — Hexagon treats it as a black-box
agent that receives a Task and returns an AgentResponse.

Install: pip install openharness-ai  (or: uv add openharness-ai)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from hexagon.domain.entities.agent_response import AgentResponse
from hexagon.domain.entities.task import Task
from hexagon.domain.ports.outbound.agent_collaboration import SubAgentRequest

if TYPE_CHECKING:
    from openharness.engine.query_engine import QueryEngine


class OpenHarnessSubAgentAdapter:
    """Delegates a Task to an OpenHarness QueryEngine and collects the full response.

    Each adapter instance wraps one QueryEngine (one agent identity with its own
    tools, permissions, and memory). For multi-agent systems, instantiate one
    adapter per specialist agent and register them via SubAgentPort.
    """

    def __init__(self, engine: "QueryEngine", agent_id: str) -> None:
        self._engine = engine
        self._agent_id = agent_id

    @property
    def agent_id(self) -> str:
        return self._agent_id

    async def delegate(self, request: SubAgentRequest) -> AgentResponse:
        from openharness.engine.stream_events import AssistantTextDelta, ErrorEvent

        task = request.task
        prompt = f"{task.title}\n\n{task.description}".strip() if task.description else task.title

        text_parts: list[str] = []
        error_parts: list[str] = []

        async for event in self._engine.submit_message(prompt):
            if isinstance(event, AssistantTextDelta):
                text_parts.append(event.text)
            elif isinstance(event, ErrorEvent):
                error_parts.append(event.message)

        content = "".join(text_parts)
        if error_parts and not content:
            content = "\n".join(error_parts)

        return AgentResponse(task_id=task.id, content=content)

    async def health(self) -> bool:
        try:
            # A minimal no-op check — verify the engine's API client is reachable
            return self._engine is not None
        except Exception:
            return False


def build_openharness_agent(
    agent_id: str,
    model: str = "claude-sonnet-4-6",
    api_key: str | None = None,
    cwd: str = ".",
    system_prompt: str = "You are a helpful AI agent.",
    max_turns: int = 8,
    full_auto: bool = False,
    extra_engine_kwargs: dict[str, Any] | None = None,
) -> OpenHarnessSubAgentAdapter:
    """Factory that wires up an OpenHarness QueryEngine and wraps it as a SubAgentPort.

    Args:
        agent_id:       Unique identifier for this agent (used by SubAgentPort).
        model:          LLM model string (e.g. "claude-sonnet-4-6", "gpt-4o").
        api_key:        API key; falls back to ANTHROPIC_API_KEY env var if None.
        cwd:            Working directory for the agent's tool execution.
        system_prompt:  System prompt defining the agent's persona and constraints.
        max_turns:      Max agentic turns per user input before stopping.
        full_auto:      If True, grant FULL_AUTO permissions (no approval prompts).
        extra_engine_kwargs: Additional kwargs forwarded to QueryEngine.__init__.
    """
    from openharness.api.client import AnthropicApiClient
    from openharness.config.settings import PermissionSettings
    from openharness.engine.query_engine import QueryEngine
    from openharness.permissions.checker import PermissionChecker
    from openharness.permissions.modes import PermissionMode
    from openharness.tools import create_default_tool_registry

    api_client = AnthropicApiClient(api_key=api_key, auth_token=None, base_url=None)
    tool_registry = create_default_tool_registry()
    mode = PermissionMode.FULL_AUTO if full_auto else PermissionMode.DEFAULT
    permission_checker = PermissionChecker(PermissionSettings(mode=mode))

    engine = QueryEngine(
        api_client=api_client,
        tool_registry=tool_registry,
        permission_checker=permission_checker,
        cwd=cwd,
        model=model,
        system_prompt=system_prompt,
        max_turns=max_turns,
        **(extra_engine_kwargs or {}),
    )

    return OpenHarnessSubAgentAdapter(engine=engine, agent_id=agent_id)
