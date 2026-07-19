# ADR-002: Synchronous Ollama Client as the Sole LLM Communication Layer

## Status

Accepted

## Context

The AI Consulting Firm system will eventually need multiple agents to
request text generation from a locally-hosted LLM served by Ollama.
Before any agent, orchestration, or prompt logic exists, the project
needs a single, well-tested integration point for talking to Ollama's
REST API — so that:

- HTTP concerns (timeouts, connection failures, status codes, JSON
  parsing) are handled in exactly one place.
- Future modules (agents, orchestration) depend on a stable,
  typed interface rather than raw HTTP calls scattered across the
  codebase.
- The integration can be fully unit tested without requiring a
  running Ollama server in CI or on developer machines.

This ADR concerns **only** the design of that integration layer
(`app/llm`). It does not cover agent design, orchestration, or memory,
which are out of scope for this module.

## Decision

1. **A single class, `OllamaClient`, is the only supported way to talk
   to Ollama.** It exposes exactly three public methods:
   `health_check()`, `list_models()`, and `generate()`. This keeps the
   surface area small and matches the actual needs of Module 1 — no
   speculative methods for functionality (streaming, embeddings, chat)
   that doesn't exist yet.

2. **The client is synchronous**, built on `httpx.Client`. The
   application does not yet have an async execution model (no FastAPI
   routes, no async orchestration), so introducing async here would
   add complexity with no current consumer. Async support can be
   added later, either as an `AsyncOllamaClient` or an async-capable
   refactor, once a concrete async caller exists.

3. **`httpx` is used over `requests`** because it offers a modern,
   well-maintained API, first-class timeout handling, and — most
   importantly for testing — `httpx.MockTransport`, which allows fully
   simulating server responses (including transport-level failures
   like connection errors and timeouts) without monkeypatching or a
   real server.

4. **All failures are translated into a dedicated exception
   hierarchy** (`LLMError` and its subclasses) rather than letting
   `httpx` exceptions or HTTP status codes leak to callers. This means
   consumers of the client never need to know it's `httpx` under the
   hood, and the underlying HTTP library could be swapped later
   without changing the public contract.

5. **`health_check()` swallows failures and returns a status object**
   instead of raising, while `list_models()` and `generate()` raise on
   failure. This reflects how each method is used: health checks are
   typically polled to *determine* availability, whereas
   `list_models()` and `generate()` represent an operation the caller
   expects to succeed, where failure is exceptional and should
   interrupt normal control flow.

6. **Configuration is sourced from the existing `app.core.config`
   settings system** (`OLLAMA_HOST`, `DEFAULT_MODEL`,
   `REQUEST_TIMEOUT`), not read independently by the client. This
   keeps a single source of truth for configuration across the
   application, consistent with the decision made in Module 0.

7. **Response payloads are parsed into typed Pydantic models**
   (`HealthStatus`, `ModelInfo`, `ModelList`, `GenerationResult`)
   rather than returned as raw dictionaries. This isolates the rest of
   the application from Ollama's specific JSON response shape.

## Alternatives Considered

- **Using `requests` instead of `httpx`.** Rejected because `httpx`'s
  `MockTransport` gives cleaner, more realistic test doubles
  (including simulating connection-level failures), and `httpx` is
  the more actively developed of the two.

- **Building an async client from the start.** Rejected for Module 1:
  there is no async caller yet, and introducing `asyncio` this early
  would add complexity the current module doesn't need. This can be
  revisited when an async consumer (e.g. a FastAPI route) is
  introduced.

- **Returning raw `dict` responses instead of typed models.**
  Rejected because it would leak Ollama's API shape into every future
  consumer of this client, making later changes to the client's
  internals (or even swapping backends) more disruptive.

- **Having `list_models()` and `generate()` also return a status
  object instead of raising.** Rejected for consistency with normal
  Python error-handling conventions: these are "expected to succeed"
  operations, and forcing every caller to check a status field instead
  of using `try`/`except` would be more error-prone.

## Consequences

- Every future module that needs to talk to an LLM (agents,
  orchestration) will depend on `app.llm.OllamaClient` rather than
  implementing its own HTTP logic, keeping LLM integration
  centralized.
- The exception hierarchy defined here becomes the contract future
  modules build error-handling around; changes to it should be made
  carefully.
- Adding async support later will likely require either a parallel
  `AsyncOllamaClient` or a breaking change to this class's interface.
  This is accepted as a reasonable future cost in exchange for
  avoiding premature complexity now.
- Because all HTTP interaction is behind `httpx.Client`, the entire
  test suite for this module runs without a real Ollama server.
