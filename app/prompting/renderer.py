"""Jinja2-based rendering of prompt templates.

:class:`PromptRenderer` is responsible only for rendering an
already-loaded template string against a variable context. It knows
nothing about the filesystem or where templates come from — that
concern lives in :mod:`app.prompting.loader`.
"""

from typing import Any

from jinja2 import (
    Environment,
    StrictUndefined,
    TemplateError,
    TemplateSyntaxError,
    UndefinedError,
)

from app.prompting.exceptions import PromptRenderingError


class PromptRenderer:
    """Renders prompt template source strings using Jinja2.

    The underlying Jinja2 environment uses
    :class:`jinja2.StrictUndefined`, so referencing a variable that was
    not supplied in the rendering context raises an error rather than
    silently rendering as an empty string — a missing variable in a
    prompt template is treated as a bug, not a cosmetic gap.
    """

    def __init__(self) -> None:
        """Initialize the renderer with a strict, autoescape-disabled environment.

        Autoescaping is disabled because prompt templates render to
        plain text (sent to an LLM), not HTML, so HTML-escaping
        template output would corrupt the resulting prompt.
        ``keep_trailing_newline`` is enabled so a template's trailing
        newline (if any) is preserved exactly rather than silently
        stripped, matching Jinja2's non-default, more predictable
        behavior for plain-text templates.
        """
        self._environment = Environment(
            undefined=StrictUndefined,
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def render(
        self, template_source: str, context: dict[str, Any] | None = None
    ) -> str:
        """Render a template source string against a variable context.

        Args:
            template_source: The raw, unrendered template text (as
                returned by :meth:`app.prompting.loader.PromptLoader.load`).
            context: Variables to make available to the template.
                Defaults to an empty context.

        Returns:
            str: The rendered text.

        Raises:
            PromptRenderingError: If the template has malformed syntax,
                references a variable missing from ``context``, or
                fails to render for any other reason.
        """
        resolved_context = context or {}

        try:
            template = self._environment.from_string(template_source)
        except TemplateSyntaxError as exc:
            raise PromptRenderingError(
                f"Malformed prompt template at line {exc.lineno}: {exc.message}"
            ) from exc

        try:
            return template.render(**resolved_context)
        except UndefinedError as exc:
            raise PromptRenderingError(f"Missing template variable: {exc}") from exc
        except TemplateError as exc:
            raise PromptRenderingError(
                f"Failed to render prompt template: {exc}"
            ) from exc
