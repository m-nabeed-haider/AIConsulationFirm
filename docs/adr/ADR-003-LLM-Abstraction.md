# ADR-003: LLM Abstraction Layer via BaseLLM and LLMFactory

## Status

Accepted

## Context

Following Module 1, the application communicated with a language
model through exactly one path:

```
Application → OllamaClient → Ollama REST API
```

This was appropriate for Module 1, whose sole goal was a clean,
well-tested integration with Ollama. However, the project's stated
long-term direction is a multi-agent system that must eventually be
able to use different LLM backends (the roadmap explicitly lists
OpenAI, Anthropic, Gemini, and vLLM as future providers) without
rewriting agent logic every time a backend changes.

If future agents were built directly against `OllamaClient`, every
agent — and any orchestration logic coordinating them — would become
coupled to Ollama specifically. Adding a second provider later would
require touching every call site, and testing agents would require
mocking Ollama-specific types instead of a stable, backend-agnostic
interface.

## Problem

How should the application depend on an LLM in a way that:

1. Lets `OllamaClient` (and its careful HTTP/error handling from
   Module 1) keep doing exactly what it already does well, and
2. Prevents any future application or agent code from depending on
   Ollama, or any other specific provider, directly, and
3. Makes adding a new provider later a localized, additive change
   rather than a cross-cutting refactor?

## Decision

Introduce an LLM abstraction layer between the application and
`OllamaClient`:

```
Application → BaseLLM → LLM Factory → Provider → OllamaClient → Ollama REST API
```

Specifically:

1. **`BaseLLM` (`app/llm/base.py`)** is an abstract base class (via
   `abc.ABC`) exposing exactly `generate()`, `health_check()`, and
   `list_models()`, with no implementation. This is the only interface
   application and (future) agent code is allowed to depend on.

2. **`OllamaProvider` (`app/llm/providers/ollama.py`)** implements
   `BaseLLM` for Ollama. It contains no HTTP logic — every method
   delegates to an injected `OllamaClient` — because that concern is
   already solved correctly in Module 1 and should not be duplicated
   or reimplemented here. The provider's only job is adapting
   `OllamaClient`'s responses to the `BaseLLM` contract (e.g. wrapping
   `GenerationResult` into `LLMResponse`) and adding timing/logging.

3. **`LLMFactory` (`app/llm/factory.py`)** is the single place that
   maps a configured provider name (`LLM_PROVIDER`) to a concrete
   `BaseLLM` implementation, via a small registry dict. Application
   code calls `LLMFactory.create()` and receives a `BaseLLM` — it
   never imports or instantiates `OllamaProvider` (or any future
   provider) directly.

4. **`LLMResponse` (`app/llm/response.py`)** is a new, provider-agnostic
   result model for `generate()` calls, decoupled from
   `OllamaClient`'s existing `GenerationResult`. It includes an open
   `metadata: dict[str, Any]` field specifically so future fields
   (token counts, finish reason, provider-specific data) can be added
   without a breaking schema change.

5. **No new exceptions are introduced.** The existing `LLMError`
   hierarchy from Module 1 is reused as-is, including for factory-level
   errors (e.g. an unsupported provider name raises `LLMError`), so
   callers only ever need to know about one exception hierarchy.

## Alternatives Considered

- **Skip the abstraction and let agents use `OllamaClient` directly.**
  Rejected: this was the situation before this module, and it
  directly conflicts with the project's stated goal of supporting
  multiple providers later without rewriting agent code.

- **Use a plugin/entry-point discovery mechanism for providers**
  (e.g. dynamically discovering provider classes via package
  metadata). Rejected as overengineering for this stage: the project
  currently has exactly one provider, and a plain dict registry in
  `LLMFactory` is trivially extensible when a second provider is
  actually added. A discovery mechanism can be introduced later if the
  number of providers or deployment scenarios genuinely demands it.

- **Have `OllamaProvider` reimplement HTTP calls to Ollama directly,
  bypassing `OllamaClient`.** Rejected: this would duplicate the
  timeout/connection/error-handling logic already built and tested in
  Module 1, violating DRY and creating two places that could drift out
  of sync.

- **Return `OllamaClient`'s existing `GenerationResult` from
  `BaseLLM.generate()` instead of introducing `LLMResponse`.**
  Rejected: `GenerationResult` is conceptually a Module 1 (transport
  layer) type. Reusing it at the abstraction layer would mean every
  future provider's output has to be shoehorned into an
  Ollama-flavored shape, undermining the point of the abstraction.

- **Introduce a new exception type for "unsupported provider"
  errors.** Rejected in favor of reusing `LLMError`, per the explicit
  instruction to avoid duplicating the exception hierarchy; the
  existing base exception already communicates "something is wrong
  with the LLM layer" without adding a new type callers must learn.

## Consequences

- Future providers (OpenAI, Anthropic, Gemini, vLLM) are added by (a)
  writing a new `app/llm/providers/<name>.py` module implementing
  `BaseLLM`, and (b) registering it in `LLMFactory._PROVIDERS` — no
  changes required to `BaseLLM`, to any other provider, or to any
  application/agent code that already depends on `BaseLLM`.
- All future agents and orchestration logic (later modules) should be
  written and tested against `BaseLLM`, not against `OllamaClient` or
  `OllamaProvider` — this ADR establishes that as the expected
  pattern going forward.
- `OllamaClient` (Module 1) is unchanged and remains the only place
  HTTP logic for Ollama lives; this module builds strictly on top of
  it rather than modifying it.
- Testing agents in future modules can rely on simple `BaseLLM`
  fakes/mocks instead of needing to simulate Ollama's HTTP API,
  simplifying future test suites.

## Decision Outcome

The application depends on an abstract LLM interface (`BaseLLM`),
obtained through `LLMFactory`, rather than on a concrete provider
implementation. `OllamaClient` continues to handle all HTTP
communication with Ollama, now one layer removed from anything the
application interacts with directly.
