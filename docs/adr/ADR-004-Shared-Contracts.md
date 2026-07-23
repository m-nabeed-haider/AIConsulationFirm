# ADR-004: Shared Typed Contracts for Cross-Subsystem Communication

## Status

Accepted

## Context

Through Module 2, the project has a clean LLM abstraction (`BaseLLM`,
`LLMFactory`) but still has no shared vocabulary for the *data* that
will flow between the components the project's long-term architecture
describes:

```
User → Supervisor Agent → Specialized Agents → LLM Abstraction → Provider → Ollama
```

Once agents, task planning, and orchestration are introduced in future
modules, these components will need to exchange things like "a unit of
work," "a message from one agent to another," and "which agent said
this." Without a shared contract for these concepts, the natural
default is to pass around plain `dict` objects or bare strings — which
is what this module exists to prevent.

## Problem

How should different subsystems (agents, planners, supervisors,
workflows, and eventually the API layer) exchange structured
information about tasks, messages, and agents, in a way that:

1. Is validated at the boundary, so malformed data fails fast with a
   clear error instead of propagating silently as a bad dictionary
   key or wrong-typed value.
2. Gives every future module a single, unambiguous definition of what
   a "task," "message," or "agent" looks like, instead of each module
   inventing its own shape.
3. Can be serialized to and from JSON cleanly, since these models will
   eventually cross process boundaries (e.g. a future API layer).
4. Can be extended over time (new fields, new enum members) without
   forcing a rewrite of every consumer.

## Decision

Every subsystem communicates through shared, strongly typed models
defined in `app/schemas`:

- **`Message`** — the unit of communication between two parties.
- **`Task`** — the unit of work.
- **`AgentInfo`** — the identity/metadata of an agent.
- **`TaskStatus`, `TaskPriority`, `MessageType`, `AgentRole`** — enums
  constraining the above models' fields to a fixed, well-known
  vocabulary.

Concretely:

1. **All models are Pydantic `BaseModel` subclasses**, giving
   automatic validation at construction time, and both `dict` and
   JSON (de)serialization for free — a natural fit given the rest of
   the codebase (`app.core.config.Settings`, `app.llm.response.
   LLMResponse`) already standardizes on Pydantic.

2. **Enums subclass both `str` and `Enum`.** This means they serialize
   to plain strings automatically (important once these models cross
   a future API boundary as JSON) while still being fully type-checked
   and comparable as enums within Python code.

3. **IDs are UUIDs, auto-generated via `default_factory=uuid4`.**
   Every model gets a globally unique identifier without callers
   needing to supply one, while still allowing an explicit ID to be
   provided (e.g. when reconstructing a model from storage in a future
   module).

4. **Timestamps are auto-generated in UTC via `default_factory`.**
   `Message.timestamp`, `Task.created_at`, and `Task.updated_at` are
   populated automatically at construction time, removing an entire
   class of "forgot to stamp the time" bugs from every future caller.

5. **This module contains no behavior.** No methods beyond Pydantic's
   built-in validation and light `field_validator`s that reject blank
   required strings. State transitions (e.g. moving a `Task` from
   `PENDING` to `IN_PROGRESS`, or updating `updated_at` on change) are
   the responsibility of whichever future module owns that logic
   (likely orchestration), not this contracts package.

6. **`app/schemas` has no dependency on any other application
   package.** These models don't import from `app.llm`, `app.core`, or
   anywhere else, keeping them safely importable from any future
   module (agents, orchestration, API) without risk of circular
   imports.

## Alternatives Considered

- **Continue passing plain `dict` objects between components.**
  Rejected: this was the implicit status quo and is exactly what this
  module exists to prevent — it defers all validation to whoever
  happens to read the dictionary, if anyone does at all.

- **Use `dataclasses` instead of Pydantic.** Rejected: dataclasses
  don't provide runtime validation or JSON (de)serialization out of
  the box, both of which these models need now (validation) and will
  need soon (serialization, once an API layer exists). Using Pydantic
  is also consistent with every other model already in the codebase.

- **Use plain `Enum` instead of `str, Enum`.** Rejected: a plain
  `Enum` serializes to something like `<TaskStatus.PENDING: 'pending'>`
  or requires `.value` everywhere; subclassing `str` as well means
  Pydantic serializes enum fields as plain strings automatically,
  which matters once these models are exchanged as JSON.

- **Give `Task` a method like `mark_completed()` that also updates
  `updated_at`.** Rejected for this module: it would introduce
  behavior into what is meant to be a pure data-contracts package.
  Such logic belongs to whatever future module actually owns task
  lifecycle transitions.

- **Make `id` required (no default) so callers must supply one
  explicitly.** Rejected: for a shared contract used across many
  future call sites, requiring every caller to generate and pass a
  UUID is unnecessary friction with no real benefit — auto-generation
  with an optional override covers both the common case and the
  reconstruction-from-storage case.

## Consequences

- Every future module (agents, orchestration, API) is expected to
  accept and return `Message`, `Task`, and `AgentInfo` instances —
  not dictionaries — at their public boundaries. Code review for
  future modules should treat a raw `dict` where one of these models
  belongs as a regression against this decision.
- Because these models are pure Pydantic contracts with no external
  dependencies, they can be unit tested (and were, in this module)
  completely in isolation, with no mocking required.
- Extending these models later — for example, adding a
  `parent_task_id` to `Task`, or a new `AgentRole` member — is a
  backward-compatible, additive change as long as new fields have
  sensible defaults, consistent with how `metadata` was added to
  `LLMResponse` in Module 2 for the same reason.
- `app.schemas` becomes a foundational, widely-imported package;
  changes to it should be made carefully, since it is expected to be a
  dependency of nearly every future module.

## Decision Outcome

Every subsystem communicates through shared typed models defined in
`app/schemas` (`Message`, `Task`, `AgentInfo`, and their supporting
enums), validated via Pydantic, rather than through raw dictionaries
or bare strings.
