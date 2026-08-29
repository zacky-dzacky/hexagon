# Hexagon

A Python framework that combines **Hexagonal Architecture** (Ports & Adapters) with **Agentic AI** systems — giving you autonomous agents that are modular, testable, and provider-agnostic.

## The Core Idea

Hexagonal Architecture (by Alistair Cockburn) says your application core should be ignorant of the outside world — databases, UIs, and third-party APIs are all plug-in adapters. Agentic AI systems have the same problem: your reasoning logic shouldn't care whether it's calling GPT-4o or Claude, hitting Pinecone or Chroma, or being driven by a REST API or CLI.

This project applies that principle rigorously to agentic systems.

---

## Are Agents Ports?

No — and this is the most important design insight.

**Agents are hexagons, not ports.** A port is an interface definition. An agent is an autonomous actor with its own domain logic, tools, and reasoning cycle. The right mapping is:

| Concept | Hexagonal Role |
|---|---|
| Agent reasoning / workflow logic | **Domain Core** |
| LLM API call (OpenAI, Anthropic, etc.) | **Outbound Secondary Adapter** |
| Tools (search, code exec, file I/O) | **Outbound Secondary Adapters** |
| Memory (short-term, long-term) | **Outbound Secondary Adapters** |
| RAG / vector retrieval | **Outbound Secondary Adapter** |
| Orchestrator (LangGraph, Prefect) | **Application Layer** |
| MCP Server (exposing agent to others) | **Inbound Primary Adapter** |
| REST API / CLI / webhook | **Inbound Primary Adapters** |
| Sub-agent (multi-agent system) | **Separate hexagon** connected via `SubAgentPort` |

The LLM call is not the brain — it is infrastructure, like a database query. It lives behind an adapter boundary. This single decision makes everything else follow.

### Multi-Agent Systems

In a multi-agent setup, each specialized agent (researcher, coder, reviewer) is its own hexagon. The orchestrator agent communicates with them through a `SubAgentPort`, which maps cleanly to the emerging [A2A protocol](https://google.github.io/A2A/). Agents are peers, not ports.

---

## Architecture

```
hexagon/
├── src/hexagon/
│   ├── domain/                   # Pure Python — zero framework imports
│   │   ├── entities/             # Value objects: Task, AgentResponse, Chunk
│   │   ├── ports/
│   │   │   ├── inbound/          # TaskHandlerPort (use-case interfaces)
│   │   │   └── outbound/         # LanguageModelPort, MemoryPort, ToolPort, SubAgentPort
│   │   └── services/             # Validation, retry logic, guardrails
│   │
│   ├── application/              # Orchestration — knows domain, not infrastructure
│   │   ├── nodes/                # Agent reasoning steps (pure functions)
│   │   ├── workflows/            # LangGraph / graph definitions
│   │   └── use_cases/            # Top-level use cases, injected with ports
│   │
│   ├── infrastructure/           # All external dependencies live here
│   │   ├── llm/                  # openai_adapter.py, anthropic_adapter.py, mock_adapter.py
│   │   ├── memory/               # redis_adapter.py, in_memory_adapter.py
│   │   ├── retrieval/            # pinecone_adapter.py, chromadb_adapter.py
│   │   ├── tools/                # brave_search_adapter.py, mcp_tool_adapter.py
│   │   └── persistence/          # postgres_adapter.py
│   │
│   ├── serving/                  # Inbound primary adapters
│   │   ├── api/                  # FastAPI routers
│   │   ├── cli/                  # Typer CLI
│   │   └── mcp_server/           # Expose this agent as an MCP server
│   │
│   └── composition/              # Single wiring point — reads config, builds the graph
│       ├── container.py
│       └── config.py
│
├── evals/                        # Quality evals (separate from unit tests)
│   └── fixtures/
│
├── tests/                        # Unit tests using mock adapters — fast, no API calls
│
├── pyproject.toml                # uv / hatch managed
└── .env.example
```

### Dependency Rule

```
serving → application → domain ← (adapters implement ports)
infrastructure → domain (implements ports, never imported by domain)
composition → everything (only wiring layer that can see all)
```

Enforced at CI time via `import-linter`. The domain layer cannot import `openai`, `anthropic`, `redis`, or any infrastructure package — this is verified on every push.

---

## Why This Matters for AI Systems

### LLM Non-Determinism Containment

LLMs hallucinate, return malformed JSON, and change behavior across API versions. Behind an adapter boundary, these failures are isolated. The domain applies retry and validation logic against the port's return type — without knowing which provider is being called.

### Provider Swapping

Swap GPT-4o for Claude, add Gemini as a fallback, or route to a local Ollama model for cost reasons — all are adapter swaps driven by config. No domain code changes.

### Fast Deterministic Testing

Agent reasoning is tested with a `MockLLMAdapter` that returns canned responses. No API costs, no flakiness, millisecond-speed test suites. Real provider integration is tested separately in evals.

### Safety as Mandatory Boundaries

Guardrails live at the port boundary — they run on every call regardless of what the agent's reasoning decided. An agent cannot skip a content filter if that filter lives in the adapter, not in an optional tool call.

### AI Coding Agent Discipline

With AI-assisted development, boundary violations propagate at scale. A human might introduce one violation per week; an AI coding agent can introduce a dozen per day by pattern-matching from existing code. `import-linter` in CI catches this automatically.

---

## Getting Started

**Prerequisites:** Python 3.14+, [uv](https://docs.astral.sh/uv/)

```bash
# Install dependencies
uv sync --extra dev

# Copy environment config
cp .env.example .env

# Run tests
uv run pytest

# Check import boundaries
uv run lint-imports
```

---

## Design Decisions

### Ports use `typing.Protocol`, not `ABC`

Python Protocols enable structural subtyping — adapters don't need to explicitly inherit from the port. This makes third-party clients easier to wrap and keeps the domain layer from pulling in adapter-specific base classes.

### `composition/` is the only layer that sees everything

`container.py` is the composition root: it reads env vars, instantiates concrete adapters, and injects them into use cases. Nothing else in the codebase imports from both `domain` and `infrastructure`.

### `evals/` is separate from `tests/`

Unit tests use mock adapters and verify logic. Evals run full workflows with real or near-real adapters and check output quality — a fundamentally different concern. They are not run in standard CI.

### MCP is a natural fit

MCP Servers expose Tools, Resources, and Prompts behind a standardized JSON-RPC contract — structurally equivalent to hexagonal secondary adapters. Any tool wrapped in an MCP server is already hexagonally isolated. The `serving/mcp_server/` layer lets this agent be consumed by other agents or hosts (Claude Desktop, VS Code, etc.).

---

## Roadmap

- [ ] Core port interfaces (`LanguageModelPort`, `MemoryPort`, `ToolPort`, `SubAgentPort`)
- [ ] Anthropic and OpenAI adapters
- [ ] In-memory mock adapters for testing
- [ ] Example agent workflow (LangGraph)
- [ ] FastAPI serving layer
- [ ] MCP server adapter
- [ ] Import boundary CI enforcement
- [ ] Multi-agent example (orchestrator + specialist agents)

---

## References

- [Hexagonal Architecture — Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
- [Applying Hexagonal Architecture in AI Agent Development](https://medium.com/@martia_es/applying-hexagonal-architecture-in-ai-agent-development-44199f6136d3)
- [Model Context Protocol Architecture](https://modelcontextprotocol.io/docs/learn/architecture)
- [A2A Protocol — Agent-to-Agent Communication](https://google.github.io/A2A/)
