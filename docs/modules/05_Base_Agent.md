# Module 5 — Base Agent Framework

## Purpose

Modules 1-4 built everything an agent needs but never assembled it:
an LLM abstraction (`BaseLLM`), a prompt management system
(`PromptManager`), and shared data contracts (`Task`, `Message`,
`AgentInfo`). This module introduces `app/agents`, providing
`BaseAgent` — the reusable class every future concrete agent
(`ResearchAgent`, `PlannerAgent`, `ReviewerAgent`, `WriterAgent`, ...)
will inherit from.

`BaseAgent`'s job is **orchestration, not business logic**: it wires
together an injected LLM and prompt manager into a fixed lifecycle
(validate → render → generate → respond). No agent-specific behavior
(what a "research" prompt should contain, how a "plan" should be
structured, etc.) lives in this module — that belongs to future,
concrete agent subclasses.

## Responsibilities

This module is responsible for:

- `BaseAgent` — the fixed orchestration lifecycle, driven entirely by
  dependency-injected `BaseLLM` and `PromptManager` instances.
- `AgentContext` — a lightweight, transient, per-execution context
  (explicitly **not** memory).
- `AgentRegistry` — an in-memory lookup of constructed agent
  instances by name, for later use by a Supervisor.
- A dedicated exception hierarchy (`AgentError`,
  `AgentExecutionError`, `InvalidTaskError`).

This module is explicitly **not** responsible for (and does not
implement): a Supervisor, LangGraph, memory, multi-agent
communication, tool calling, RAG, or FastAPI. It also does not
implement any concrete agent (no `ResearchAgent`, etc.) — those are
future work built on top of `BaseAgent`.

## Architecture

```
app/agents/
├── __init__.py       # Public exports
├── exceptions.py       # AgentError, AgentExecutionError, InvalidTaskError
├── context.py             # AgentContext
├── base.py                   # BaseAgent
└── registry.py                  # AgentRegistry
```

```
Caller
  │
  │  constructs and injects
  ▼
BaseLLM  ──┐
           ├──►  BaseAgent.execute(task, context) ──► Message
PromptManager ──┘
```

`BaseAgent` depends only on the abstractions introduced in earlier
modules — `app.llm.base.BaseLLM` and
`app.prompting.manager.PromptManager` — never on a concrete
implementation such as `OllamaProvider` or `OllamaClient`. Both are
supplied by the caller via the constructor (dependency injection);
`BaseAgent` never constructs either itself. This keeps `BaseAgent`
fully testable with mocks and free of any provider-specific or
prompt-storage-specific assumptions.

## Execution Lifecycle

`BaseAgent.execute(task, context=None, receiver="caller")` performs,
in order:

1. **Validate** the task (`validate_task`) — checks it is a genuine
   `Task` with a status eligible for execution (`PENDING` or
   `IN_PROGRESS`); raises `InvalidTaskError` otherwise.
2. **Build prompt context** (`build_prompt_context`) — maps the task
   (and execution context) onto the variables the agent's prompt
   template expects. The default implementation exposes only
   `task_title` and `task_description`; subclasses override this to
   shape their own template's variables.
3. **Render** the agent's configured prompt template via the injected
   `PromptManager`; a `PromptError` is wrapped as `AgentExecutionError`.
4. **Generate** a completion via the injected `BaseLLM`; an `LLMError`
   is wrapped as `AgentExecutionError`.
5. **Return** the result as a `Message`, with `sender` set to the
   agent's name, `content` set to the LLM's generated text, and
   `message_type` set to `RESPONSE`.

## Public API

### `BaseAgent` (`app/agents/base.py`)

```python
agent = BaseAgent(
    metadata=AgentInfo(name="Ava", role=AgentRole.RESEARCH_ANALYST),
    llm=llm,                     # a BaseLLM instance, injected
    prompt_manager=prompts,      # a PromptManager instance, injected
    prompt_template="system/research",
)
message = agent.execute(task)
```

| Member | Description |
|---|---|
| `metadata: AgentInfo` | Identity of the agent (name, role, description) — reuses the Module 3 `AgentInfo` model rather than duplicating it. |
| `execute(task, context=None, receiver="caller") -> Message` | Runs the full lifecycle described above. |
| `validate_task(task) -> None` | Overridable hook; default checks type and status. |
| `build_prompt_context(task, context) -> dict[str, Any]` | Overridable hook; default exposes `task_title`/`task_description`. |

Subclassing example (illustrative only — not implemented in this
module):

```python
class ResearchAgent(BaseAgent):
    def build_prompt_context(self, task, context):
        return {"company_name": "AI Consulting Firm", "topic": task.title}
```

### `AgentContext` (`app/agents/context.py`)

| Field | Type | Default |
|---|---|---|
| `conversation_id` | `UUID` | auto-generated |
| `execution_id` | `UUID` | auto-generated |
| `metadata` | `dict[str, Any]` | `{}` |

Purely transient — nothing here is persisted or read back across
calls. Memory (recall across executions) is out of scope for this
module.

### `AgentRegistry` (`app/agents/registry.py`)

| Method | Description |
|---|---|
| `register(agent: BaseAgent) -> None` | Registers an agent by `agent.metadata.name`. Raises `AgentError` on duplicate names. |
| `unregister(name: str) -> None` | Removes a registered agent. Raises `AgentError` if not found. |
| `get(name: str) -> BaseAgent` | Retrieves a registered agent. Raises `AgentError` if not found. |
| `list_agents() -> list[AgentInfo]` | Returns metadata for every registered agent. |

The registry holds constructed agent instances in memory; it performs
no discovery or construction of its own. It exists for a future
Supervisor (not implemented here) to look up agents by name.

### Exceptions (`app/agents/exceptions.py`)

| Exception | Raised when |
|---|---|
| `AgentError` | Base class; also raised directly for registry errors. |
| `InvalidTaskError` | The task passed to `execute()` is not a valid, executable `Task`. |
| `AgentExecutionError` | Prompt rendering or LLM generation fails during a valid task's execution. |

## Configuration

None. This module introduces no new environment variables or
settings.

## Acceptance Criteria

- [x] `BaseAgent` is implemented, orchestrating `BaseLLM` and
      `PromptManager` through a fixed lifecycle.
- [x] Dependency injection is used throughout — `BaseAgent` never
      instantiates `PromptManager` or `BaseLLM` internally (verified by
      a dedicated test asserting no concrete provider is referenced in
      `app/agents/base.py`'s source).
- [x] `AgentRegistry` is implemented with `register()`, `unregister()`,
      `get()`, and `list_agents()`.
- [x] `AgentContext` is implemented as a lightweight, non-memory
      per-execution context.
- [x] Unit tests cover the `execute()` lifecycle, prompt rendering,
      LLM invocation, message creation, registry behavior, and invalid
      task handling — all fully mocked, no Ollama or external service
      required (190 tests passing across the whole project).
- [x] Documentation (this file) and ADR-006 are complete.
- [x] `PROJECT_ROADMAP.md` is updated to mark Module 5 complete.
