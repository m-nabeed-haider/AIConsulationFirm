# Module 1 — Ollama Client

## Purpose

This module introduces `app/llm`, a package that provides
`OllamaClient`: the single, synchronous communication layer between
the application and a local [Ollama](https://ollama.com) server. No
other part of the application is permitted to issue HTTP requests to
Ollama directly — everything goes through this client.

This module intentionally implements **only** the HTTP integration
layer. It does not include agents, orchestration, memory, prompt
templates, or any business logic — those are left to later modules.

## Package Layout

```
app/llm/
├── __init__.py     # Public exports
├── client.py        # OllamaClient implementation
├── exceptions.py     # LLMError hierarchy
└── models.py          # Typed request/response data models
```

## Public API

### `OllamaClient`

```python
from app.llm import OllamaClient

client = OllamaClient()
```

The client reads its configuration from the application's existing
settings system (`app.core.config.get_settings`) by default, but also
accepts an explicit `Settings` instance and/or an existing
`httpx.Client` for dependency injection (primarily used in tests).

It exposes exactly three public methods:

| Method | Description |
|---|---|
| `health_check() -> HealthStatus` | Checks whether the Ollama server is reachable. Never raises — failures are reported in the returned `HealthStatus`. |
| `list_models() -> ModelList` | Retrieves the models currently available on the Ollama server. |
| `generate(prompt: str, model: str \| None = None) -> GenerationResult` | Generates a text completion for the given prompt, using `model` if provided, otherwise the configured default model. |

The client also implements `close()` and the context manager protocol
(`__enter__` / `__exit__`) to release its underlying HTTP connection
pool.

### Data Models (`app/llm/models.py`)

- `HealthStatus` — result of a connectivity check.
- `ModelInfo` / `ModelList` — metadata about available models.
- `GenerationResult` — the output of a `generate()` call.

These models decouple the rest of the application from Ollama's raw
JSON response shapes.

### Exceptions (`app/llm/exceptions.py`)

All errors raised by the client inherit from `LLMError`:

- `LLMError` — base exception for the LLM integration layer.
- `OllamaConnectionError` — the server could not be reached.
- `OllamaTimeoutError` — the request exceeded the configured timeout.
- `ModelNotFoundError` — the requested model does not exist on the
  server.

Callers that don't need to distinguish failure modes can simply catch
`LLMError`.

## Configuration

The client is configured entirely through `app.core.config.Settings`,
which reads the following environment variables:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Base URL of the Ollama server. |
| `DEFAULT_MODEL` | `llama3` | Model used when `generate()` is called without an explicit model. |
| `REQUEST_TIMEOUT` | `30` | Request timeout, in seconds. |

See `.env.example` for the template.

## Usage Example

```python
from app.llm import OllamaClient
from app.llm.exceptions import LLMError

with OllamaClient() as client:
    status = client.health_check()
    if not status.is_available:
        print(f"Ollama is not available: {status.message}")
    else:
        try:
            result = client.generate(prompt="Explain recursion in one sentence.")
            print(result.response)
        except LLMError as exc:
            print(f"Generation failed: {exc}")
```

## Explicit Non-Goals (Module 1)

The following are **not** implemented in this module, by design:

- Streaming responses
- Async support
- Embeddings
- Chat history / conversation state
- Prompt templates
- Retry logic
- Tool calling

These may be introduced in future modules as separate, focused units
of work.

## Testing

See [`docs/testing/01_Testing_Strategy.md`](../testing/01_Testing_Strategy.md)
for how this module is tested without a running Ollama instance.
