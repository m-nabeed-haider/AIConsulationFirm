"""Unit tests for :class:`app.prompting.loader.PromptLoader`.

Every test uses pytest's ``tmp_path`` fixture to build an isolated,
disposable prompt directory, so none of these tests touch the real
``prompts/`` directory or depend on Ollama or any external service.
"""

from pathlib import Path

import pytest

from app.prompting.exceptions import PromptError, PromptNotFoundError
from app.prompting.loader import PromptLoader


@pytest.fixture
def prompt_dir(tmp_path: Path) -> Path:
    """Build a small, isolated prompt directory tree for testing.

    Args:
        tmp_path: Pytest's built-in temporary directory fixture.

    Returns:
        Path: Root of a temporary prompt directory containing a few
        known template files.
    """
    (tmp_path / "system").mkdir()
    (tmp_path / "user").mkdir()

    (tmp_path / "system" / "research.md").write_text(
        "# Research\n\nTopic: {{ topic }}\n", encoding="utf-8"
    )
    (tmp_path / "system" / "planner.md").write_text(
        "# Planner\n\nIdea: {{ idea }}\n", encoding="utf-8"
    )
    (tmp_path / "user" / "greeting.md").write_text(
        "Hello, {{ name }}!\n", encoding="utf-8"
    )

    return tmp_path


class TestLoad:
    """Tests for PromptLoader.load()."""

    def test_load_existing_template_returns_raw_content(self, prompt_dir: Path) -> None:
        """Loading an existing template should return its exact raw content."""
        loader = PromptLoader(prompt_dir=prompt_dir)

        content = loader.load("system/research")

        assert content == "# Research\n\nTopic: {{ topic }}\n"

    def test_load_accepts_explicit_md_extension(self, prompt_dir: Path) -> None:
        """A template name with an explicit .md suffix should also work."""
        loader = PromptLoader(prompt_dir=prompt_dir)

        content = loader.load("system/research.md")

        assert content == "# Research\n\nTopic: {{ topic }}\n"

    def test_load_nested_subdirectory_template(self, prompt_dir: Path) -> None:
        """Templates in subdirectories should be addressable by relative path."""
        loader = PromptLoader(prompt_dir=prompt_dir)

        content = loader.load("user/greeting")

        assert "Hello" in content

    def test_load_missing_template_raises_prompt_not_found_error(
        self, prompt_dir: Path
    ) -> None:
        """Loading a template that does not exist should raise PromptNotFoundError."""
        loader = PromptLoader(prompt_dir=prompt_dir)

        with pytest.raises(PromptNotFoundError):
            loader.load("system/does_not_exist")

    def test_load_path_traversal_attempt_raises_prompt_not_found_error(
        self, prompt_dir: Path
    ) -> None:
        """A template name attempting to escape the prompt directory should be rejected."""
        loader = PromptLoader(prompt_dir=prompt_dir)

        with pytest.raises(PromptNotFoundError):
            loader.load("../outside")

    def test_load_from_nonexistent_prompt_directory_raises_not_found(
        self, tmp_path: Path
    ) -> None:
        """Loading from a prompt directory that doesn't exist on disk should raise."""
        loader = PromptLoader(prompt_dir=tmp_path / "does_not_exist")

        with pytest.raises(PromptNotFoundError):
            loader.load("system/research")


class TestExists:
    """Tests for PromptLoader.exists()."""

    def test_returns_true_for_existing_template(self, prompt_dir: Path) -> None:
        """exists() should return True for a template that is present."""
        loader = PromptLoader(prompt_dir=prompt_dir)

        assert loader.exists("system/research") is True

    def test_returns_false_for_missing_template(self, prompt_dir: Path) -> None:
        """exists() should return False, not raise, for a missing template."""
        loader = PromptLoader(prompt_dir=prompt_dir)

        assert loader.exists("system/nonexistent") is False

    def test_returns_false_for_path_traversal_attempt(self, prompt_dir: Path) -> None:
        """exists() should return False, not raise, for an escaping path."""
        loader = PromptLoader(prompt_dir=prompt_dir)

        assert loader.exists("../outside") is False


class TestListTemplates:
    """Tests for PromptLoader.list_templates()."""

    def test_lists_all_templates_without_extension(self, prompt_dir: Path) -> None:
        """All .md files should be listed, without their extension, sorted."""
        loader = PromptLoader(prompt_dir=prompt_dir)

        templates = loader.list_templates()

        assert templates == ["system/planner", "system/research", "user/greeting"]

    def test_returns_empty_list_for_empty_directory(self, tmp_path: Path) -> None:
        """An existing but empty prompt directory should yield an empty list."""
        loader = PromptLoader(prompt_dir=tmp_path)

        assert loader.list_templates() == []

    def test_returns_empty_list_for_nonexistent_directory(self, tmp_path: Path) -> None:
        """A prompt directory that doesn't exist should yield an empty list, not raise."""
        loader = PromptLoader(prompt_dir=tmp_path / "does_not_exist")

        assert loader.list_templates() == []

    def test_ignores_non_markdown_files(self, prompt_dir: Path) -> None:
        """Non-.md files in the prompt directory should not appear in the listing."""
        (prompt_dir / "system" / "notes.txt").write_text(
            "not a prompt", encoding="utf-8"
        )
        loader = PromptLoader(prompt_dir=prompt_dir)

        templates = loader.list_templates()

        assert "system/notes" not in templates


class TestMalformedFileHandling:
    """Tests for handling filesystem-level read failures gracefully."""

    def test_unreadable_file_raises_prompt_error(self, prompt_dir: Path) -> None:
        """A file that exists but cannot be decoded as UTF-8 should raise PromptError."""
        binary_path = prompt_dir / "system" / "binary.md"
        binary_path.write_bytes(b"\xff\xfe\x00\x01invalid-utf8")
        loader = PromptLoader(prompt_dir=prompt_dir)

        with pytest.raises(PromptError):
            loader.load("system/binary")
