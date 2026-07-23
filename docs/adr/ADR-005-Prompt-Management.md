# ADR-005: Prompt Templates as External Markdown Files Rendered via Jinja2

## Status

Accepted

## Context

Through Module 3, the project has an LLM abstraction (`BaseLLM`) and a
shared vocabulary for domain data (`Message`, `Task`, `AgentInfo`),
but no established mechanism for managing prompt *content*. Future
agents (Module 5+) will each need one or more prompts describing their
role, objective, and instructions — text that is fundamentally
different in nature from application logic: it's natural-language
content, iterated on by prompt engineering rather than software
engineering, and often needs to change independently of the code that
uses it.

If prompt text were embedded directly as Python string literals or
f-strings inside agent code, several problems follow:

- Editing a prompt requires touching Python source and going through
  the same review/deploy path as code changes, even for a purely
  wording change.
- Prompt text becomes harder to diff meaningfully in code review,
  mixed in with indentation, escaping, and string concatenation noise.
- There is no single place to see all prompts used by the system, or
  to reuse a common instruction fragment across multiple prompts.
- Non-engineers (e.g. someone iterating purely on prompt wording)
  would need to read and modify Python to change a prompt.

## Problem

How should prompt content be authored, stored, and turned into the
final text sent to an LLM, in a way that:

1. Keeps prompt engineering fully separate from application logic.
2. Supports variable substitution (e.g. inserting a task description
   or topic into a prompt) and light control flow (e.g. optional
   sections), without requiring bespoke string-formatting code
   scattered across the codebase.
3. Fails loudly and specifically when a prompt is malformed or a
   required variable is missing, rather than silently producing a
   broken or incomplete prompt.
4. Is simple enough not to overengineer a concern that, at this stage,
   is "render some text from a template" — nothing more.

## Decision

Prompt templates are maintained as external Markdown (`.md`) files
under `prompts/`, rendered through Jinja2, via a small dedicated
subsystem (`app/prompting`):

1. **Templates are plain `.md` files, not Python code.** They live
   under `prompts/system/`, `prompts/user/`, and `prompts/shared/`,
   organized by the role of prompt they represent. No prompt text is
   permitted to be a Python string literal in agent or application
   code — this module exists specifically to remove that possibility.

2. **Jinja2 is the rendering engine.** It is a mature, widely
   understood templating library that supports variable substitution
   and the light control flow (`{% if %}`, `{% for %}`) prompts
   occasionally need (e.g. an optional list of focus areas), without
   requiring a bespoke templating format to be designed and
   maintained.

3. **Three focused classes, not one.** `PromptLoader` (filesystem
   access), `PromptRenderer` (Jinja2 rendering), and `PromptManager`
   (the public facade composing both, plus caching). This follows the
   single-responsibility pattern already established in Module 1/2
   (`OllamaClient` vs. `BaseLLM`/`OllamaProvider`): each piece has one
   reason to change, and `PromptManager` is the one class the rest of
   the application is expected to depend on.

4. **Rendering uses Jinja2's `StrictUndefined`.** Referencing a
   template variable that isn't supplied in the rendering context
   raises an error immediately, rather than silently rendering as an
   empty string. A missing prompt variable is treated as a bug to
   surface immediately, not a cosmetic gap to render around — this
   matters more for prompts than for, say, a web page, since a
   silently-blank prompt section can materially change what an LLM is
   asked to do without any visible error.

5. **A dedicated exception hierarchy** (`PromptError`,
   `PromptNotFoundError`, `PromptRenderingError`), mirroring the
   pattern already established for the LLM layer in Module 1
   (`LLMError` and subclasses), so callers have one place to catch
   prompt-related failures.

6. **`PromptManager` never communicates with an LLM.** Its
   responsibility ends at producing rendered text; passing that text
   to `BaseLLM.generate()` is the responsibility of whichever future
   module (agents) actually needs a completion. This keeps the
   dependency direction one-way: agents will depend on both
   `app.prompting` and `app.llm`, but `app.prompting` depends on
   neither `app.llm` nor any agent code.

7. **A lightweight in-memory cache in `PromptManager`.** Template
   *source* (not rendered output, since that depends on the context)
   is cached after first load, avoiding repeated disk reads for
   templates rendered many times in a session. This is a small,
   easily reasoned-about optimization — not a general-purpose caching
   framework — and can be disabled via `PromptManager(use_cache=False)`
   or cleared via `clear_cache()`.

## Alternatives Considered

- **Embed prompts as Python string constants or f-strings.** Rejected
  as the exact problem this ADR exists to avoid — see Context above.

- **Store prompts as `.txt`, `.j2`, or `.jinja` files instead of
  `.md`.** Rejected: `.md` renders readably in any editor or Git host
  even before substitution, and prompt authors are very likely already
  comfortable writing Markdown for structuring instructions (headers,
  bullet lists), which most of these prompts naturally use.

- **Use Python's built-in `string.Template` or f-string-style
  formatting instead of Jinja2.** Rejected: neither supports
  conditional sections or loops, both of which are common needs for
  prompts (e.g. "include this section only if X was provided"),
  without hand-rolled pre/post-processing logic that Jinja2 already
  provides.

- **Store prompts in a database or as YAML/JSON with prompt text as a
  field.** Rejected as premature for this stage: the project has no
  database yet (deliberately — see Modules 0–3), and plain files
  under version control are sufficient for prompt content that is
  edited by humans and reviewed like any other source artifact.

- **Use Jinja2's default `Undefined` (lenient) instead of
  `StrictUndefined`.** Rejected: lenient undefined values silently
  render as empty strings, which could produce a plausible-looking but
  subtly broken prompt (e.g. a missing topic silently disappearing
  from a research prompt) with no error to catch the mistake.

- **Merge loading and rendering into a single class.** Rejected in
  favor of `PromptLoader` + `PromptRenderer` composed by
  `PromptManager`: keeping filesystem access and template rendering
  as separate, independently testable concerns is consistent with the
  single-responsibility approach used elsewhere in this codebase.

## Consequences

- Every future agent that needs a prompt is expected to render it via
  `PromptManager.render(name, context)` and treat the result as
  opaque, fully-formed text — no future module should construct
  prompt text through Python string manipulation.
- Adding, editing, or reviewing a prompt becomes a Markdown-file
  change, reviewable independently of application code changes.
- Because `StrictUndefined` is used, every template must be paired
  with callers that supply its full set of required variables;
  templates that want a variable to be genuinely optional must guard
  it explicitly with `is defined` in the template itself.
- `app/prompting` becomes a foundational dependency for future agent
  modules, alongside `app/llm` and `app/schemas`, but does not itself
  depend on either — preserving a clean, one-directional dependency
  graph.

## Decision Outcome

Prompt templates are maintained as external Markdown files under
`prompts/`, rendered through Jinja2 via `PromptManager`, rather than
embedded directly in Python source code.
