# AI Consulting Firm — Project Roadmap

This document tracks module-by-module progress toward the full
multi-agent AI Consulting Firm platform. It is the source of truth for
what has been built, what is in progress, and what remains.

## Current Phase

**Phase: Base Agent Framework — Module 5 complete.**
Next up: with `BaseAgent` in place, future modules can implement
concrete agents (Research, Planner, Reviewer, Writer, ...) on top of
it, and eventually a Supervisor to coordinate them via
`AgentRegistry`.

## Module Status

| Module | Name | Status | Summary |
|--------|------|--------|---------|
| 0 | Project Foundation | ✅ Complete | Project scaffold, configuration, logging, tests. |
| 1 | Ollama Client | ✅ Complete | `OllamaClient`: the HTTP integration layer with a local Ollama server. |
| 2 | LLM Abstraction Layer | ✅ Complete | `BaseLLM`, `LLMFactory`, `LLMResponse`, and `OllamaProvider` decouple the application from any specific LLM backend. |
| 3 | Shared Data Models | ✅ Complete | `Message`, `Task`, `AgentInfo`, and supporting enums — the typed contracts every future subsystem communicates through. |
| 4 | Prompt Management System | ✅ Complete | `PromptManager`, `PromptLoader`, and `PromptRenderer` — prompts live as external Markdown templates rendered via Jinja2, never embedded in Python source. |
| 5 | Base Agent Framework | ✅ Complete | `BaseAgent`, `AgentContext`, and `AgentRegistry` — the reusable orchestration lifecycle (validate → render → generate → respond) every future concrete agent inherits from. |
| 6 | *Future* | ⬜ Not started | To be scoped. |
| 7 | *Future* | ⬜ Not started | To be scoped. |

Exact module boundaries and ordering beyond Module 5 are subject to
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

### Module 4 — Prompt Management System ✅

Introduced `app/prompting`, separating prompt engineering from
application logic entirely:

- `PromptLoader` — locates and reads `.md` template files from the
  configured prompt directory (`prompts/`, organized into `system/`,
  `user/`, and `shared/`).
- `PromptRenderer` — renders template text via Jinja2, using
  `StrictUndefined` so a missing variable raises immediately rather
  than rendering blank.
- `PromptManager` — the public facade composing both, adding template
  existence checks, listing, and in-memory caching of raw template
  source. Never communicates with an LLM.
- `PromptError`, `PromptNotFoundError`, `PromptRenderingError` — a
  dedicated exception hierarchy, mirroring Module 1's `LLMError`
  pattern.
- Three example system templates ship with this module:
  `prompts/system/research.md`, `planner.md`, `reviewer.md`.

See [`docs/modules/04_Prompt_Manager.md`](docs/modules/04_Prompt_Manager.md)
and [`docs/adr/ADR-005-Prompt-Management.md`](docs/adr/ADR-005-Prompt-Management.md)
for full details.

### Module 5 — Base Agent Framework ✅

Introduced `app/agents`, the reusable orchestration base every future
concrete agent inherits from:

- `BaseAgent` — a fixed execution lifecycle (validate task → build
  prompt context → render prompt → call the LLM → return a
  `Message`), built entirely on dependency-injected `BaseLLM` and
  `PromptManager` instances. Never constructs either itself.
- `AgentContext` — a lightweight, transient per-execution context
  (explicitly not memory).
- `AgentRegistry` — an in-memory `register()`/`unregister()`/`get()`/
  `list_agents()` lookup of constructed agents by name, for later use
  by a Supervisor.
- `AgentError`, `AgentExecutionError`, `InvalidTaskError` — a
  dedicated exception hierarchy, wrapping failures from the
  orchestrated prompt and LLM layers.

No concrete agents (Research, Planner, Reviewer, Writer, etc.) are
implemented yet — this module provides only the reusable base they
will build on.

See [`docs/modules/05_Base_Agent.md`](docs/modules/05_Base_Agent.md)
and [`docs/adr/ADR-006-Base-Agent.md`](docs/adr/ADR-006-Base-Agent.md)
for full details.

## Explicit Non-Goals (as of Module 5)

The following remain unimplemented, reserved for future modules, and
should not be assumed present when building on top of this codebase:

- LangGraph / multi-agent orchestration
- A Supervisor, or any multi-agent coordination
- Concrete business agents (Research Analyst, Project Manager,
  Reviewer, etc.) — only the reusable `BaseAgent` they will inherit
  from exists so far
- Memory systems (short-term, long-term, or vector-based)
- Tool calling
- Retrieval-augmented generation (RAG)
- FastAPI routes / HTTP API layer
- Streaming responses
- Async support
- Databases
- Vector stores
- Chat history / conversation memory
