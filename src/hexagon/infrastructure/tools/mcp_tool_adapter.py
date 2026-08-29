from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.types import Tool as MCPTool

from hexagon.domain.ports.outbound.tool import ToolDefinition, ToolResult


class MCPToolAdapter:
    """Wraps a single MCP tool from a stdio server as a ToolPort.

    Keeps a persistent session open across calls; call `close()` or use as
    an async context manager when the adapter is no longer needed.
    """

    def __init__(self, session: ClientSession, tool: MCPTool) -> None:
        self._session = session
        self._tool = tool
        self._definition = ToolDefinition(
            name=tool.name,
            description=tool.description or "",
            parameters=tool.inputSchema or {},
        )

    @property
    def definition(self) -> ToolDefinition:
        return self._definition

    async def execute(self, tool_call_id: str, arguments: dict[str, Any]) -> ToolResult:
        result = await self._session.call_tool(self._tool.name, arguments)
        content = "\n".join(
            block.text if hasattr(block, "text") else str(block)
            for block in result.content
        )
        return ToolResult(
            tool_call_id=tool_call_id,
            name=self._tool.name,
            content=content,
            is_error=result.isError or False,
        )


class MCPServerConnection:
    """Opens a stdio MCP server and exposes each of its tools as MCPToolAdapters."""

    def __init__(self, server_params: StdioServerParameters) -> None:
        self._server_params = server_params
        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None
        self.tools: list[MCPToolAdapter] = []

    async def connect(self) -> None:
        read, write = await self._stack.enter_async_context(stdio_client(self._server_params))
        self._session = await self._stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()
        result = await self._session.list_tools()
        self.tools = [MCPToolAdapter(self._session, t) for t in result.tools]

    async def close(self) -> None:
        await self._stack.aclose()

    async def __aenter__(self) -> "MCPServerConnection":
        await self.connect()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
