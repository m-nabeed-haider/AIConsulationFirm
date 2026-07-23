# Module 4 — Prompt Management System

## Purpose

Through Module 3, the project has a stable data vocabulary but no
established way to manage the actual prompt text that will eventually
be sent to an LLM. Without a dedicated subsystem, the natural failure
mode is prompt strings creeping directly into Python source — mixing
prompt engineering with application logic, making prompts hard to
review, version, or edit without touching code.

This module introduces `app/prompting`, a subsystem that separates
prompt engineering from application logic entirely: **prompt templates
live as external Markdown files, never as strings embedded in Python
code.** Future agents render a named template through
`PromptManager` and receive back plain text — they never see a raw
prompt string in `.py` source.

## Responsibilities

This module is responsible for:

- Locating and reading prompt template files from disk
  (`PromptLoader`).
- Rendering template text against a variable context using Jinja2
  (`PromptRenderer`).
- Providing a single public entry point (`PromptManager`) that
  composes the two, plus template existence checks, listing, and
  in-memory caching.
- Shipping a handful of example system templates
  (`prompts/system/research.md`, `planner.md`, `reviewer.md`).

This module is explicitly **not** responsible for (and does not
implement): agents, LangGraph, memory, tool calling, FastAPI, RAG,
streaming, or async support. `PromptManager` never communicates with
an LLM — it turns a template name and a context into rendered text,
nothing more.

## Architecture

```
app/prompting/
├── __init__.py      # Public exports
├── exceptions.py      # PromptError hierarchy
├── loader.py             # PromptLoader — filesystem access only
├── renderer.py              # PromptRenderer — Jinja2 rendering only
└── manager.py                  # PromptManager — public facade, composes the above

prompts/
├── system/          # System-role prompt templates
│   ├── research.md
│   ├── planner.md
│   └── reviewer.md
├── user/             # (reserved) user-role prompt templates
└── shared/            # (reserved) partials/fragments shared across templates
```

```
Caller (future agent, service, etc.)
        ↓
  PromptManager           ← the only class other code should use
        ↓            ↓
PromptLoader   PromptRenderer
    ↓                  ↓
Filesystem      Jinja2 Environment
(prompts/*.md)
```

`PromptLoader` and `PromptRenderer` are deliberately kept separate and
composed by `PromptManager`, rather than merged into one class: the
loader knows only about the filesystem, the renderer knows only about
Jinja2, and neither has any reason to change because of the other.

## Public API

### `PromptManager` (`app/prompting/manager.py`)

```python
from app.prompting import PromptManager

prompts = PromptManager()
```

| Method | Description |
|---|---|
| `load(name: str) -> str` | Return the raw, unrendered template source. |
| `render(name: str, context: dict \| None = None) -> str` | Load and render a template against `context`. |
| `exists(name: str) -> bool` | Check whether a template exists. |
| `list_templates() -> list[str]` | List all available template names (relative path, no `.md` extension). |
| `clear_cache() -> None` | Clear the in-memory cache of loaded template source. |

Template names are given relative to the prompt root, with or without
the `.md` extension — e.g. `"system/research"` or
`"system/research.md"`.

By default, `PromptManager` caches raw template source in memory after
the first `load()`/`render()` call for a given name, so repeatedly
rendering the same template (with different contexts) does not re-read
the file from disk each time. This can be disabled via
`PromptManager(use_cache=False)`.

### Exceptions (`app/prompting/exceptions.py`)

| Exception | Raised when |
|---|---|
| `PromptError` | Base class for all prompt-subsystem errors. |
| `PromptNotFoundError` | The requested template name does not correspond to any `.md` file. |
| `PromptRenderingError` | The template has malformed Jinja2 syntax, or references a variable missing from the supplied context. |

### `PromptLoader` and `PromptRenderer`

These are used internally by `PromptManager` and are also directly
importable (`app.prompting.loader.PromptLoader`,
`app.prompting.renderer.PromptRenderer`) for cases where composing
them differently is useful (e.g. tests). Application code should
prefer `PromptManager` over using these directly.

## Template Structure

Templates are plain Markdown files using Jinja2 syntax for variable
substitution and control flow:

```markdown
# Role

You are a **Research Analyst** at {{ company_name }}, an AI consulting firm.

# Objective

Research the following topic: {{ topic }}

{% if focus_areas is defined and focus_areas %}
# Focus Areas
{% for area in focus_areas %}
- {{ area }}
{% endfor %}
{% endif %}
```

Two conventions matter for every template:

1. **Required variables** (e.g. `topic`, `company_name`) are referenced
   directly with `{{ variable }}`. The rendering environment uses
   Jinja2's `StrictUndefined`, so omitting a required variable from
   the context raises `PromptRenderingError` rather than silently
   rendering blank — a missing prompt variable is a bug, not a
   cosmetic gap.
2. **Optional variables** (e.g. `focus_areas`, `constraints`) must be
   guarded with `is defined` — `{% if focus_areas is defined and
   focus_areas %}` — since `StrictUndefined` raises even inside an
   `{% if %}` test if the name doesn't exist in the context at all.

Templates are organized by role:

- `prompts/system/` — system-role prompts defining an agent's
  persona and instructions (three examples shipped with this module).
- `prompts/user/` — reserved for user-role prompt templates.
- `prompts/shared/` — reserved for reusable partials/fragments
  included by other templates.

## Configuration

One new environment variable:

| Variable | Default | Description |
|---|---|---|
| `PROMPT_DIR` | `prompts` | Root directory containing prompt templates. Relative paths are resolved against the project root. |

See `.env.example`. No other configuration was introduced.

## Usage Example

```python
from app.prompting import PromptManager, PromptError

prompts = PromptManager()

try:
    system_prompt = prompts.render(
        "system/research",
        {
            "company_name": "AI Consulting Firm",
            "topic": "local LLM adoption in small businesses",
            "focus_areas": ["cost", "data privacy"],
        },
    )
except PromptError as exc:
    print(f"Failed to prepare prompt: {exc}")
else:
    print(system_prompt)
```

Note that `PromptManager` returns plain rendered text — passing it to
an LLM is the responsibility of a future module (agents), not this
one.

## Acceptance Criteria

- [x] `PromptManager` loads templates (`load()`).
- [x] `PromptManager` renders templates (`render()`), including
      existence checks (`exists()`) and listing (`list_templates()`).
- [x] Prompt templates live entirely outside Python source, as `.md`
      files under `prompts/`.
- [x] Custom exceptions (`PromptError`, `PromptNotFoundError`,
      `PromptRenderingError`) are implemented and used consistently.
- [x] Rendering is powered by Jinja2, with strict handling of missing
      variables.
- [x] `PromptManager` never communicates with an LLM.
- [x] Comprehensive unit tests cover loading, rendering, missing
      templates, missing variables, malformed templates, and caching
      — all without depending on Ollama or any external service (144
      tests passing across the whole project).
- [x] Documentation (this file) and ADR-005 are complete.
- [x] `PROJECT_ROADMAP.md` is updated to mark Module 4 complete.
