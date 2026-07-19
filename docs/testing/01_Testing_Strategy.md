# Testing Strategy — Module 1: Ollama Client

## Goal

Verify the behavior of `app.llm.client.OllamaClient` — including its
success paths, error handling, and configuration wiring — **without**
requiring a running Ollama instance, either locally or in CI.

## Approach: Transport-Level Mocking

`OllamaClient` is built on `httpx.Client`. Rather than mocking
individual methods on the client (which would test implementation
details), tests inject a fake transport using
[`httpx.MockTransport`](https://www.python-httpx.org/advanced/transports/#mock-transports).

A `MockTransport` takes a handler function that receives the outgoing
`httpx.Request` and returns the `httpx.Response` the fake server
should send back — or raises an `httpx` exception to simulate a
transport-level failure (e.g. a dropped connection or timeout).

```python
def handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"models": []})

transport = httpx.MockTransport(handler)
http_client = httpx.Client(base_url="http://testserver", transport=transport)
client = OllamaClient(settings=test_settings, http_client=http_client)
```

This approach is preferred over patching `httpx.Client.request` with
`unittest.mock` because:

- It exercises the *real* `httpx.Client` request/response machinery
  (headers, URL building, JSON encoding), catching integration bugs
  that a pure method-level mock would miss.
- It can simulate connection errors and timeouts realistically, by
  raising the same exception types `httpx` would raise in production.
- It keeps tests decoupled from `OllamaClient`'s internal
  implementation (e.g. which private method issues the request),
  making the tests robust to refactoring.

## Dependency Injection for Testability

`OllamaClient.__init__` accepts an optional `http_client:
httpx.Client | None` parameter. In production, the client builds its
own `httpx.Client` from configuration. In tests, a client backed by a
`MockTransport` is injected instead. This is the only seam the tests
rely on — no monkeypatching of internals, no network access.

Similarly, `__init__` accepts an optional `settings: Settings | None`,
allowing tests to construct isolated `Settings` instances (fixed host,
model, and timeout values) instead of depending on the real process
environment or `.env` file.

## What Is Tested

Tests live in `tests/llm/test_client.py`, organized by method:

- **`health_check()`**
  - Returns `is_available=True` on a successful response.
  - Returns `is_available=False` (does not raise) on connection
    errors, timeouts, and server error responses.

- **`list_models()`**
  - Parses a populated model list correctly.
  - Handles an empty model list.
  - Raises `OllamaConnectionError` on connection failure.
  - Raises `OllamaTimeoutError` on timeout.
  - Raises `LLMError` on unexpected server errors and malformed JSON.

- **`generate()`**
  - Returns a correctly parsed `GenerationResult` on success.
  - Uses the configured default model when none is specified.
  - Uses an explicitly provided model when specified, and sends it in
    the request body.
  - Raises `ModelNotFoundError` on a 404 response.
  - Raises `OllamaConnectionError` on connection failure.
  - Raises `OllamaTimeoutError` on timeout.
  - Raises `LLMError` on other unexpected server errors.

- **Client lifecycle**
  - Configuration (host, default model) is correctly sourced from
    `Settings`.
  - The client can be used as a context manager, closing its
    underlying HTTP client on exit.

## Running the Tests

```bash
pytest tests/llm/ -v
```

Or, to run the full project test suite (Module 0 + Module 1):

```bash
pytest -v
```

No environment variables, `.env` file, or network access are required
— all configuration used in tests is constructed explicitly via the
`make_settings()` helper in the test module.

## Non-Goals of This Testing Effort

- **No integration tests against a real Ollama server.** These may be
  introduced later as a separate, explicitly-marked test suite (e.g.
  `tests/integration/`), gated behind an environment flag so they
  don't run by default in CI.
- **No performance or load testing** of the client.
- **No testing of functionality this module doesn't implement**
  (streaming, async, embeddings, retries, etc.) — see
  [`docs/modules/01_Ollama_Client.md`](../modules/01_Ollama_Client.md)
  for the explicit list of non-goals.
