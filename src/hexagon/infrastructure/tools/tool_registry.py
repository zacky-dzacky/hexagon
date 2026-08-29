from hexagon.domain.ports.outbound.tool import ToolDefinition, ToolPort


class ToolRegistry:
    """Concrete ToolRegistryPort — holds a flat list of ToolPort instances."""

    def __init__(self, tools: list[ToolPort] | None = None) -> None:
        self._tools: dict[str, ToolPort] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: ToolPort) -> None:
        self._tools[tool.definition.name] = tool

    def get_tools(self) -> list[ToolPort]:
        return list(self._tools.values())

    def get_definitions(self) -> list[ToolDefinition]:
        return [t.definition for t in self._tools.values()]

    def get(self, name: str) -> ToolPort | None:
        return self._tools.get(name)
