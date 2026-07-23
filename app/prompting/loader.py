"""Filesystem access to prompt templates.

:class:`PromptLoader` is responsible only for locating and reading
prompt template files from disk. It knows nothing about Jinja2 or
rendering — that concern lives in :mod:`app.prompting.renderer`.
"""

from pathlib import Path

from app.core.config import Settings, get_settings
from app.prompting.exceptions import PromptError, PromptNotFoundError

_TEMPLATE_EXTENSION: str = ".md"


class PromptLoader:
    """Locates and reads prompt template files from the prompt directory.

    All prompt templates are external Markdown (``.md``) files living
    under a configured root directory (see
    :attr:`app.core.config.Settings.prompt_dir`), organized into
    ``system/``, ``user/``, and ``shared/`` subdirectories. Templates
    are referred to by name relative to that root, with or without the
    ``.md`` extension (e.g. ``"system/research"`` or
    ``"system/research.md"``).
    """

    def __init__(self, prompt_dir: Path | str | None = None) -> None:
        """Initialize the loader.

        Args:
            prompt_dir: Root directory to resolve template names
                against. Defaults to the directory configured via
                :attr:`app.core.config.Settings.prompt_dir`, resolved
                relative to the project root. Primarily overridden in
                tests to point at an isolated temporary directory.
        """
        self._prompt_dir: Path = (
            Path(prompt_dir) if prompt_dir is not None else self._resolve_default_dir()
        )

    @property
    def prompt_dir(self) -> Path:
        """Path: The root directory this loader resolves template names against."""
        return self._prompt_dir

    def exists(self, template_name: str) -> bool:
        """Check whether a prompt template exists.

        Args:
            template_name: Name of the template, with or without the
                ``.md`` extension (e.g. ``"system/research"``).

        Returns:
            bool: True if a corresponding ``.md`` file exists under
            the prompt directory, False otherwise.
        """
        try:
            path = self._resolve_path(template_name)
        except PromptNotFoundError:
            return False
        return path.is_file()

    def load(self, template_name: str) -> str:
        """Read the raw, unrendered contents of a prompt template.

        Args:
            template_name: Name of the template, with or without the
                ``.md`` extension (e.g. ``"system/research"``).

        Returns:
            str: The raw template source, exactly as stored on disk.

        Raises:
            PromptNotFoundError: If no ``.md`` file corresponds to
                ``template_name`` under the prompt directory.
            PromptError: If the file exists but cannot be read (e.g.
                due to a filesystem or encoding error).
        """
        path = self._resolve_path(template_name)

        if not path.is_file():
            raise PromptNotFoundError(
                f"Prompt template '{template_name}' was not found under "
                f"'{self._prompt_dir}'."
            )

        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise PromptError(
                f"Failed to read prompt template '{template_name}' at '{path}': {exc}"
            ) from exc

    def list_templates(self) -> list[str]:
        """List all available prompt templates.

        Returns:
            list[str]: Template names relative to the prompt
            directory, without the ``.md`` extension (e.g.
            ``"system/research"``), sorted alphabetically. Returns an
            empty list if the prompt directory does not exist.
        """
        if not self._prompt_dir.is_dir():
            return []

        return sorted(
            path.relative_to(self._prompt_dir).with_suffix("").as_posix()
            for path in self._prompt_dir.rglob(f"*{_TEMPLATE_EXTENSION}")
            if path.is_file()
        )

    def _resolve_path(self, template_name: str) -> Path:
        """Resolve a template name to an absolute path within the prompt directory.

        Args:
            template_name: Name of the template, with or without the
                ``.md`` extension.

        Returns:
            Path: The absolute path the template name resolves to.

        Raises:
            PromptNotFoundError: If the resolved path would fall
                outside the configured prompt directory (e.g. via a
                ``../`` path traversal attempt).
        """
        normalized_name = (
            template_name
            if template_name.endswith(_TEMPLATE_EXTENSION)
            else f"{template_name}{_TEMPLATE_EXTENSION}"
        )

        prompt_dir_resolved = self._prompt_dir.resolve()
        candidate_path = (self._prompt_dir / normalized_name).resolve()

        if (
            prompt_dir_resolved not in candidate_path.parents
            and candidate_path != prompt_dir_resolved
        ):
            raise PromptNotFoundError(
                f"Prompt template '{template_name}' resolves outside of the "
                f"configured prompt directory."
            )

        return candidate_path

    @staticmethod
    def _resolve_default_dir() -> Path:
        """Resolve the default prompt directory from application settings.

        Returns:
            Path: The absolute path to the configured prompt
            directory. Relative paths are resolved against the
            project root.
        """
        settings: Settings = get_settings()
        configured_path = Path(settings.prompt_dir)

        if configured_path.is_absolute():
            return configured_path

        project_root = Path(__file__).resolve().parents[2]
        return project_root / configured_path
