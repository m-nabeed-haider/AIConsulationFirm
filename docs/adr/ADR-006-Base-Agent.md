# ADR-006: A Common, Reusable BaseAgent for Every Future AI Agent

## Status

Accepted

## Context

By Module 4, the project has every building block an agent needs but
nothing that assembles them: `BaseLLM` (Module 2) provides
provider-agnostic generation, `PromptManager` (Module 4) provides
externalized, renderable prompt templates, and `app.schemas` (Module
3) provides the shared `Task`, `Message`, and `AgentInfo` contracts
those pieces should communicate through.

The project's roadmap calls for multiple future agents — a Research
Analyst, Project Manager/Planner, Reviewer, Software Engineer, and
others — each with different responsibilities and prompt content, but
all doing fundamentally the same *mechanical* thing: take a task,
turn it into a prompt, ask an LLM, and produce a message back. Without
a shared base, each future agent would reimplement that same
mechanical sequence — task validation, prompt rendering, LLM
invocation, response wrapping, and error handling — independently,
with no guarantee of consistency, and no single place to fix a bug in
that sequence once it exists in five different agents.

## Problem

How should the mechanical, repeated parts of "an agent processes a
task" be implemented once, shared by every future agent, while still
allowing each agent to bring its own domain-specific behavior — and
without prematurely building the parts of a multi-agent system
(supervision, memory, tool calling) that later modules are meant to
own?

## Decision

Introduce `BaseAgent` (`app/agents/base.py`), a single reusable class
every future agent inherits from, encapsulating exactly the mechanical
orchestration lifecycle and nothing else:

1. **`BaseAgent.execute()` implements a fixed, five-step lifecycle**:
   validate the task, build the prompt context, render the prompt,
   call the LLM, and return a `Message`. This sequence itself is not
   something individual agents should be free to reorder or skip
   steps of — consistency here is exactly the point of having a base
   class.

2. **Dependency injection for both `BaseLLM` and `PromptManager`.**
   `BaseAgent.__init__` accepts both as constructor arguments and
   never constructs either internally. This means `BaseAgent` has zero
   knowledge of which LLM provider or prompt-storage configuration is
   in use — consistent with the abstraction boundaries established in
   Module 2 (`LLMFactory`) and Module 4 (`PromptManager`) — and makes
   `BaseAgent` trivially testable with mocks, as demonstrated by this
   module's test suite.

3. **Exactly two overridable hooks carry agent-specific behavior**:
   `build_prompt_context()` (required for any agent whose template
   needs more than generic task title/description) and
   `validate_task()` (optional, for agent-specific validation beyond
   the generic checks `BaseAgent` already performs). Everything else
   about the lifecycle is fixed. This is a deliberately narrow
   extension surface: it's enough for a `ResearchAgent` to shape its
   own template variables without needing to override `execute()`
   itself, but it does not let subclasses silently skip validation or
   invent a different lifecycle.

4. **`BaseAgent` reuses `AgentInfo` (Module 3) for its metadata**,
   rather than defining a parallel metadata shape. `name`, `role`, and
   `description` — the fields requested for "agent metadata" — are
   exactly what `AgentInfo` already provides, and reusing it keeps
   agent identity consistent with the shared contracts decision in
   ADR-004.

5. **`AgentContext` is explicitly not memory.** It carries a
   `conversation_id`, `execution_id`, and free-form `metadata` for a
   single `execute()` call — useful for logging/tracing correlation —
   but nothing in it is read from or written to any store. Actual
   memory (recall of prior conversation state) is left to a future
   module, so this module doesn't have to make premature decisions
   about memory's shape or storage.

6. **`AgentRegistry` is a plain in-memory dict keyed by agent name**,
   exposing only `register()`, `unregister()`, `get()`, and
   `list_agents()`. It performs no agent construction, discovery, or
   dispatch — it exists solely so a future Supervisor can look up
   agents by name, without this module needing to anticipate how
   supervision or dispatch will actually work.

7. **Failures from the orchestrated subsystems are wrapped, not
   passed through raw.** A `PromptError` or `LLMError` raised while
   executing a task becomes an `AgentExecutionError`, so callers of
   `BaseAgent.execute()` only need to know about the agent-layer
   exception hierarchy, not reach into `app.prompting` or `app.llm`'s
   exceptions directly.

## Alternatives Considered

- **Make `BaseAgent` an abstract base class (`abc.ABC`) requiring
  subclasses to implement `execute()` themselves.** Rejected: this
  would push the entire mechanical lifecycle — the part that should be
  identical across agents — into every subclass, defeating the purpose
  of a shared base. `BaseAgent` is deliberately concrete and
  immediately usable; subclasses override narrow hooks, not the whole
  lifecycle.

- **Have `BaseAgent` construct its own `PromptManager`/`BaseLLM`
  internally (e.g. via `LLMFactory.create()` and `PromptManager()`
  defaults).** Rejected per explicit instruction and for the same
  reason Module 2's `LLMFactory` exists: a hardcoded internal
  construction would silently couple every agent to specific
  configuration/provider choices and make agents much harder to unit
  test in isolation.

- **Give `BaseAgent` its own metadata model instead of reusing
  `AgentInfo`.** Rejected: `AgentInfo` (Module 3) already defines
  exactly `name`, `role`, `description` (plus `id`); introducing a
  second, parallel shape would violate the shared-contracts decision
  in ADR-004 for no benefit.

- **Fold `AgentContext` and memory together into one concept now.**
  Rejected: conflating "data about this one execution" with "recall
  across executions" would force premature decisions about memory's
  design before a dedicated module addresses it. Keeping
  `AgentContext` deliberately minimal keeps this module's scope honest.

- **Let `AgentRegistry` also be responsible for constructing agents
  (e.g. from configuration).** Rejected as overreach for this module:
  construction requires knowing about concrete LLMs, prompt managers,
  and templates — decisions that belong to whatever future module
  (likely a Supervisor or application bootstrap) actually wires agents
  together. The registry here only tracks already-constructed
  instances.

## Consequences

- Every future concrete agent (`ResearchAgent`, `PlannerAgent`,
  `ReviewerAgent`, `WriterAgent`, and others) is expected to subclass
  `BaseAgent` and override `build_prompt_context()` (and, where
  needed, `validate_task()`) rather than reimplementing task
  validation, prompt rendering, or LLM invocation from scratch.
- A bug fix or behavior change to the core execution lifecycle (e.g.
  improved error handling, added logging) is made once in `BaseAgent`
  and benefits every agent automatically.
- Because `BaseAgent` depends only on `BaseLLM` and `PromptManager`
  (both abstractions), swapping the underlying LLM provider (Module 2)
  or prompt storage mechanism (Module 4) requires no changes to
  `BaseAgent` or any agent built on top of it.
- `AgentRegistry`, in its current minimal form, becomes a building
  block a future Supervisor module can depend on directly, without
  this module having committed to any particular supervision or
  dispatch strategy.

## Decision Outcome

All future AI agents inherit from a common, reusable `BaseAgent` that
orchestrates dependency-injected `BaseLLM` and `PromptManager`
instances through a fixed execution lifecycle, rather than each agent
independently reimplementing task validation, prompt rendering, LLM
invocation, and response construction.
