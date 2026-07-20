# Module 2 — LLM Abstraction Layer

## Purpose

Module 1 introduced `OllamaClient`, a clean HTTP integration with a
local Ollama server — but application code (and, eventually, agents)
would still depend on that concrete client directly. This module
introduces an abstraction layer so that **no code above the provider
layer ever depends on Ollama, or any specific LLM backend, directly.**

Future agents, orchestration, and services depend only on
`BaseLLM`, obtained through `LLMFactory`. Swapping or adding a
provider (OpenAI, Anthropic, Gemini, vLLM, ...) will not require
changes to any code that consumes an LLM.

## Responsibilities

This module is responsible for:

- Defining the provider-agnostic `BaseLLM` contract.
- Providing a concrete `OllamaProvider` that satisfies that contract
  by delegating to the existing `OllamaClient`.
- Providing an `LLMFactory` that constructs the correct provider based
  on configuration (`LLM_PROVIDER`).
- Defining `LLMResponse`, a provider-agnostic result type for
  generation calls.

This module is **not** responsible for (and does not implement):
LangGraph, agents, memory, prompt templates, tool calling, RAG,
FastAPI, streaming, async support, databases, vector stores, or chat
history. Those belong to later modules.

## Architecture Diagram

Before this module:

```
Application
      ↓
OllamaClient
      ↓
Ollama REST API
```

After this module:

```
Application
      ↓
   BaseLLM            <- application/agent code depends on this only
      ↓
  LLM Factory         <- reads LLM_PROVIDER, picks a provider
      ↓
   Provider           <- e.g. OllamaProvider (adapter, no HTTP logic)
      ↓
  OllamaClient        <- Module 1: all HTTP logic lives here
      ↓
 Ollama REST API
```

```
app/llm/
├── __init__.py          # Public exports (BaseLLM, LLMFactory, LLMResponse, ...)
├── base.py               # BaseLLM — the abstract contract
├── factory.py             # LLMFactory — provider selection
├── response.py             # LLMResponse — provider-agnostic result model
├── client.py                # OllamaClient (Module 1, unchanged)
├── exceptions.py              # LLMError hierarchy (Module 1, unchanged)
├── models.py                    # HealthStatus / ModelList / etc. (Module 1, unchanged)
│
└── providers/
    ├── __init__.py
    └── ollama.py            # OllamaProvider — BaseLLM implementation for Ollama
```

## Public API

### `BaseLLM` (`app/llm/base.py`)

Abstract base class (via `abc.ABC`). Cannot be instantiated directly.
Defines exactly three abstract methods that every provider must
implement:

| Method | Returns | Description |
|---|---|---|
| `generate(prompt: str)` | `LLMResponse` | Generate a text completion. |
| `health_check()` | `HealthStatus` | Check provider availability. |
| `list_models()` | `ModelList` | List models available from the provider. |

### `OllamaProvider` (`app/llm/providers/ollama.py`)

Implements `BaseLLM` for Ollama. Contains **no HTTP logic** — every
method delegates to an injected `OllamaClient` instance. Its only
added responsibilities are:

- Adapting `OllamaClient.generate()`'s `GenerationResult` into an
  `LLMResponse`.
- Measuring generation duration.
- Logging provider, model, duration, and success/failure (never
  prompt content).
- Letting exceptions from `OllamaClient` propagate unchanged.

### `LLMFactory` (`app/llm/factory.py`)

```python
from app.llm import LLMFactory

llm = LLMFactory.create()  # reads LLM_PROVIDER from settings
response = llm.generate("Explain recursion in one sentence.")
```

Internally, `LLMFactory` holds a registry (`_PROVIDERS: dict[str,
type[BaseLLM]]`) mapping a provider name to a provider class. Adding a
new provider in a future module means adding one entry to that dict —
no changes to `LLMFactory.create()`'s logic, and no changes to any
caller.

An unsupported `LLM_PROVIDER` value raises `LLMError` (reused from
Module 1 — no new exception types were introduced by this module).

### `LLMResponse` (`app/llm/response.py`)

```python
class LLMResponse(BaseModel):
    text: str
    model: str
    duration: float
    created_at: datetime
    metadata: dict[str, Any]  # extension point for future fields
```

The `metadata` field exists specifically so future data — token
counts, finish reason, provider-specific details — can be attached
without changing this model's core shape or breaking existing
consumers.

## Configuration

One new environment variable, added to the existing settings system:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | Identifies which registered provider `LLMFactory` should construct. |

All other configuration (`OLLAMA_HOST`, `DEFAULT_MODEL`,
`REQUEST_TIMEOUT`) is unchanged from Module 1 and continues to be read
by `OllamaClient`.

## Usage Example

```python
from app.llm import LLMFactory, LLMError

llm = LLMFactory.create()

status = llm.health_check()
if not status.is_available:
    print(f"LLM provider unavailable: {status.message}")
else:
    try:
        response = llm.generate("Summarize the benefits of local LLMs.")
        print(response.text)
    except LLMError as exc:
        print(f"Generation failed: {exc}")
```

Note that this code has no reference to Ollama, `httpx`, or any
transport detail — it depends entirely on `BaseLLM` and `LLMFactory`.

## Acceptance Criteria

- [x] Application code depends on `BaseLLM` instead of `OllamaClient`.
- [x] `OllamaProvider` implements `BaseLLM` and wraps `OllamaClient`
      with no HTTP logic of its own.
- [x] `LLMFactory` returns the correct provider based on
      `LLM_PROVIDER`, and is trivially extensible to new providers.
- [x] `LLMResponse` exists and supports forward-compatible extension
      via `metadata`.
- [x] Existing Module 0 and Module 1 functionality continues to work
      unchanged (all 45 tests pass, including the pre-existing ones).
- [x] Unit tests cover `BaseLLM` abstractness, provider delegation,
      factory behavior (valid and invalid providers), `LLMResponse`
      validation, and exception propagation — none require a running
      Ollama instance.
- [x] Documentation (this file) and ADR-003 are complete.
- [x] `PROJECT_ROADMAP.md` is updated to mark Module 2 complete.
