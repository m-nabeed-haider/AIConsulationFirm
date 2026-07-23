"""Custom exceptions for the prompt management subsystem.

All errors raised by :mod:`app.prompting` are instances of
:class:`PromptError` (or one of its subclasses). Callers should catch
:class:`PromptError` when they do not need to distinguish between
failure modes.
"""


class PromptError(Exception):
    """Base exception for all errors raised by the prompt management subsystem.

    Every other exception in :mod:`app.prompting` inherits from this
    class, allowing callers to catch a single exception type when they
    do not need to distinguish between failure modes.
    """


class PromptNotFoundError(PromptError):
    """Raised when a requested prompt template does not exist.

    This is raised when a template name does not correspond to any
    ``.md`` file under the configured prompt directory.
    """


class PromptRenderingError(PromptError):
    """Raised when a prompt template fails to render.

    This covers both malformed template syntax (e.g. an unclosed
    Jinja2 tag) and missing template variables required by the
    template but not supplied in the rendering context.
    """
