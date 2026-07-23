"""Public entry point for the prompt management subsystem.

:class:`PromptManager` is the only class other application code
(future agents, orchestration, services) should use to work with
prompt templates. It composes :class:`app.prompting.loader.PromptLoader`
(filesystem access) and :class:`app.prompting.renderer.PromptRenderer`
(Jinja2 rendering), and is responsible only for loading and rendering
templates — it never communicates with an LLM.
"""

from typing import Any

from app.core.logger import logger
from app.prompting.loader import PromptLoader
from app.prompting.renderer import PromptRenderer


class PromptManager:
    """Loads and renders prompt templates stored as external Markdown files.

    Prompt engineering is kept entirely out of Python source: template
    content lives under the configured prompt directory (``system/``,
    ``user/``, and ``shared/`` subdirectories), and this class is
    responsible only for finding, reading, and rendering those files.
    It performs no LLM communication of any kind.
    """

    def __init__(
        self,
        loader: PromptLoader | None = None,
        renderer: PromptRenderer | None = None,
        use_cache: bool = True,
    ) -> None:
        """Initialize the manager.

        Args:
            loader: The :class:`PromptLoader` to use for filesystem
                access. Defaults to a new loader built from
                application settings.
            renderer: The :class:`PromptRenderer` to use for
                rendering. Defaults to a new renderer.
            use_cache: Whether to cache raw template source in memory
                after the first load, avoiding repeated disk reads for
                templates rendered multiple times. Defaults to True.
        """
        self._loader = loader or PromptLoader()
        self._renderer = renderer or PromptRenderer()
        self._use_cache = use_cache
        self._cache: dict[str, str] = {}

    def exists(self, name: str) -> bool:
        """Check whether a prompt template exists.

        Args:
            name: Name of the template, with or without the ``.md``
                extension (e.g. ``"system/research"``).

        Returns:
            bool: True if the template exists, False otherwise.
        """
        return self._loader.exists(name)

    def list_templates(self) -> list[str]:
        """List all prompt templates available under the prompt directory.

        Returns:
            list[str]: Template names, without the ``.md`` extension,
            sorted alphabetically.
        """
        return self._loader.list_templates()

    def load(self, name: str) -> str:
        """Load the raw, unrendered source of a prompt template.

        Args:
            name: Name of the template, with or without the ``.md``
                extension (e.g. ``"system/research"``).

        Returns:
            str: The raw template source.

        Raises:
            app.prompting.exceptions.PromptNotFoundError: If no
                template corresponds to ``name``.
            app.prompting.exceptions.PromptError: If the template
                exists but cannot be read.
        """
        if self._use_cache and name in self._cache:
            logger.debug("Prompt template '{}' loaded from cache.", name)
            return self._cache[name]

        content = self._loader.load(name)

        if self._use_cache:
            self._cache[name] = content

        logger.debug("Prompt template '{}' loaded from disk.", name)
        return content

    def render(self, name: str, context: dict[str, Any] | None = None) -> str:
        """Load and render a prompt template against a variable context.

        Args:
            name: Name of the template, with or without the ``.md``
                extension (e.g. ``"system/research"``).
            context: Variables to make available to the template.
                Defaults to an empty context.

        Returns:
            str: The rendered prompt text.

        Raises:
            app.prompting.exceptions.PromptNotFoundError: If no
                template corresponds to ``name``.
            app.prompting.exceptions.PromptRenderingError: If the
                template is malformed or references a variable missing
                from ``context``.
        """
        template_source = self.load(name)
        rendered = self._renderer.render(template_source, context)

        logger.info("Rendered prompt template '{}'.", name)
        return rendered

    def clear_cache(self) -> None:
        """Clear the in-memory cache of loaded template source.

        Subsequent calls to :meth:`load` or :meth:`render` will read
        the corresponding template from disk again. Useful in tests,
        or if templates are expected to change on disk during the
        lifetime of a long-running process.
        """
        self._cache.clear()
