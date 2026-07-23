# AI Consulting Firm — Project Roadmap

This document tracks module-by-module progress toward the full
multi-agent AI Consulting Firm platform. It is the source of truth for
what has been built, what is in progress, and what remains.

## Current Phase

**Phase: Shared Contracts — Module 3 complete.**
Next up: the platform now has a stable data vocabulary (`Message`,
`Task`, `AgentInfo`); future modules can begin building agents,
planning, and orchestration logic on top of it.

## Module Status

| Module | Name | Status | Summary |
|--------|------|--------|---------|
| 0 | Project Foundation | ✅ Complete | Project scaffold, configuration, logging, tests. |
| 1 | Ollama Client | ✅ Complete | `OllamaClient`: the HTTP integration layer with a local Ollama server. |
| 2 | LLM Abstraction Layer | ✅ Complete | `BaseLLM`, `LLMFactory`, `LLMResponse`, and `OllamaProvider` decouple the application from any specific LLM backend. |
| 3 | Shared Data Models | ✅ Complete | `Message`, `Task`, `AgentInfo`, and supporting enums — the typed contracts every future subsystem communicates through. |
| 4 | *Future* | ⬜ Not started | To be scoped. |
| 5 | *Future* | ⬜ Not started | To be scoped. |
| 6 | *Future* | ⬜ Not started | To be scoped. |
| 7 | *Future* | ⬜ Not started | To be scoped. |

Exact module boundaries and ordering beyond Module 3 are subject to
change as the project evolves; see
[`docs/10_Future_Work.md`](docs/10_Future_Work.md) for open-ended
notes on future direction.

## Module Details

### Module 0 — Project Foundation ✅

Established the enterprise project scaffold: package layout, typed
configuration (`app/core/config.py`), centralized Loguru logging,
`.env` handling, base tests, and initial documentation structure. No
AI, agents, or business logic.

### Module 1 — Ollama Client ✅

Introduced `app/llm/client.py`'s `OllamaClient`: the sole HTTP
communication layer with a local Ollama server, using `httpx`. Added
a custom exception hierarchy (`LLMError` and subclasses), typed
response models (`HealthStatus`, `ModelList`, `GenerationResult`), and
a fully mocked test suite requiring no running Ollama instance.

### Module 2 — LLM Abstraction Layer ✅

Introduced an abstraction layer so application and future agent code
never depends on Ollama (or any specific provider) directly:

- `BaseLLM` — the abstract contract (`generate`, `health_check`,
  `list_models`).
- `OllamaProvider` — implements `BaseLLM` by delegating to the
  existing `OllamaClient`; contains no HTTP logic of its own.
- `LLMFactory` — constructs the configured provider (`LLM_PROVIDER`
  environment variable), extensible to future providers (OpenAI,
  Anthropic, Gemini, vLLM) via a simple registry.
- `LLMResponse` — a provider-agnostic result model with a `metadata`
  extension point for future fields.

See [`docs/modules/02_LLM_Abstraction.md`](docs/modules/02_LLM_Abstraction.md)
and [`docs/adr/ADR-003-LLM-Abstraction.md`](docs/adr/ADR-003-LLM-Abstraction.md)
for full details.

### Module 3 — Shared Data Models ✅

Introduced `app/schemas`, the package defining the typed contracts
every future subsystem (agents, planners, supervisors, workflows, and
the eventual API layer) must use to communicate, instead of raw
dictionaries or strings:

- `Message` — a unit of communication between two parties.
- `Task` — a unit of work, with lifecycle status and priority.
- `AgentInfo` — an agent's identity and role.
- `TaskStatus`, `TaskPriority`, `MessageType`, `AgentRole` — the
  enums constraining the above models' fields.

All models are Pydantic-based, auto-generate their `id` (UUID) and
timestamp fields, and contain no AI logic, persistence, or business
behavior — contracts only.

See [`docs/modules/03_Shared_Data_Models.md`](docs/modules/03_Shared_Data_Models.md)
and [`docs/adr/ADR-004-Shared-Contracts.md`](docs/adr/ADR-004-Shared-Contracts.md)
for full details.

## Explicit Non-Goals (as of Module 3)

The following remain unimplemented, reserved for future modules, and
should not be assumed present when building on top of this codebase:

- LangGraph / multi-agent orchestration
- Agents of any kind (Supervisor, Research Analyst, etc.)
- Memory systems (short-term, long-term, or vector-based)
- Prompt templates / prompt management
- Tool calling
- Retrieval-augmented generation (RAG)
- FastAPI routes / HTTP API layer
- Streaming responses
- Async support
- Databases
- Vector stores
- Chat history / conversation memory
