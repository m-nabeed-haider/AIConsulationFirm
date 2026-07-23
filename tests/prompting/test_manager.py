"""Unit tests for :class:`app.prompting.manager.PromptManager`.

These tests use a real :class:`PromptLoader` pointed at an isolated
``tmp_path`` directory for end-to-end coverage, plus a mocked loader
to precisely verify caching behavior (call counts). Nothing here
touches Ollama or any external service.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.prompting.exceptions import PromptNotFoundError, PromptRenderingError
from app.prompting.loader import PromptLoader
from app.prompting.manager import PromptManager


@pytest.fixture
def prompt_dir(tmp_path: Path) -> Path:
    """Build a small, isolated prompt directory tree for testing.

    Args:
        tmp_path: Pytest's built-in temporary directory fixture.

    Returns:
        Path: Root of a temporary prompt directory containing a
        known template file.
    """
    (tmp_path / "system").mkdir()
    (tmp_path / "system" / "greeting.md").write_text(
        "Hello, {{ name }}! Welcome to {{ company }}.\n", encoding="utf-8"
    )
    return tmp_path


class TestLoadAndRender:
    """End-to-end tests using a real PromptLoader over a temp directory."""

    def test_load_returns_raw_template_source(self, prompt_dir: Path) -> None:
        """load() should return the unrendered template source."""
        manager = PromptManager(loader=PromptLoader(prompt_dir=prompt_dir))

        content = manager.load("system/greeting")

        assert "{{ name }}" in content

    def test_render_substitutes_context_variables(self, prompt_dir: Path) -> None:
        """render() should load and render the template in one step."""
        manager = PromptManager(loader=PromptLoader(prompt_dir=prompt_dir))

        result = manager.render(
            "system/greeting", {"name": "Ada", "company": "AI Consulting Firm"}
        )

        assert result == "Hello, Ada! Welcome to AI Consulting Firm.\n"

    def test_render_missing_template_raises_prompt_not_found_error(
        self, prompt_dir: Path
    ) -> None:
        """Rendering a nonexistent template should raise PromptNotFoundError."""
        manager = PromptManager(loader=PromptLoader(prompt_dir=prompt_dir))

        with pytest.raises(PromptNotFoundError):
            manager.render("system/does_not_exist", {})

    def test_render_missing_variable_raises_prompt_rendering_error(
        self, prompt_dir: Path
    ) -> None:
        """Rendering with an incomplete context should raise PromptRenderingError."""
        manager = PromptManager(loader=PromptLoader(prompt_dir=prompt_dir))

        with pytest.raises(PromptRenderingError):
            manager.render("system/greeting", {"name": "Ada"})  # missing "company"

    def test_exists_delegates_to_loader(self, prompt_dir: Path) -> None:
        """exists() should reflect whether the underlying template file exists."""
        manager = PromptManager(loader=PromptLoader(prompt_dir=prompt_dir))

        assert manager.exists("system/greeting") is True
        assert manager.exists("system/does_not_exist") is False

    def test_list_templates_delegates_to_loader(self, prompt_dir: Path) -> None:
        """list_templates() should reflect the templates present on disk."""
        manager = PromptManager(loader=PromptLoader(prompt_dir=prompt_dir))

        assert manager.list_templates() == ["system/greeting"]


class TestCaching:
    """Tests for PromptManager's in-memory template cache."""

    def test_repeated_load_uses_cache_by_default(self) -> None:
        """A second load() of the same template should not hit the loader again."""
        mock_loader = MagicMock(spec=PromptLoader)
        mock_loader.load.return_value = "Hello, {{ name }}!"
        manager = PromptManager(loader=mock_loader)

        manager.load("system/greeting")
        manager.load("system/greeting")

        mock_loader.load.assert_called_once_with("system/greeting")

    def test_render_also_benefits_from_cache(self) -> None:
        """render() should reuse cached template source across multiple calls."""
        mock_loader = MagicMock(spec=PromptLoader)
        mock_loader.load.return_value = "Hello, {{ name }}!"
        manager = PromptManager(loader=mock_loader)

        manager.render("system/greeting", {"name": "Ada"})
        manager.render("system/greeting", {"name": "Bo"})

        mock_loader.load.assert_called_once_with("system/greeting")

    def test_different_templates_are_cached_independently(self) -> None:
        """Loading two distinct templates should hit the loader once per template."""
        mock_loader = MagicMock(spec=PromptLoader)
        mock_loader.load.side_effect = lambda name: f"content for {name}"
        manager = PromptManager(loader=mock_loader)

        manager.load("system/a")
        manager.load("system/b")
        manager.load("system/a")

        assert mock_loader.load.call_count == 2

    def test_clear_cache_forces_reload_from_loader(self) -> None:
        """clear_cache() should cause the next load() to hit the loader again."""
        mock_loader = MagicMock(spec=PromptLoader)
        mock_loader.load.return_value = "Hello, {{ name }}!"
        manager = PromptManager(loader=mock_loader)

        manager.load("system/greeting")
        manager.clear_cache()
        manager.load("system/greeting")

        assert mock_loader.load.call_count == 2

    def test_cache_disabled_reloads_every_time(self) -> None:
        """With use_cache=False, every load() call should hit the loader."""
        mock_loader = MagicMock(spec=PromptLoader)
        mock_loader.load.return_value = "Hello, {{ name }}!"
        manager = PromptManager(loader=mock_loader, use_cache=False)

        manager.load("system/greeting")
        manager.load("system/greeting")

        assert mock_loader.load.call_count == 2

    def test_cache_does_not_mask_not_found_errors(self) -> None:
        """A PromptNotFoundError should not be cached as if it were valid content."""
        mock_loader = MagicMock(spec=PromptLoader)
        mock_loader.load.side_effect = PromptNotFoundError("missing")
        manager = PromptManager(loader=mock_loader)

        with pytest.raises(PromptNotFoundError):
            manager.load("system/missing")
        with pytest.raises(PromptNotFoundError):
            manager.load("system/missing")

        assert mock_loader.load.call_count == 2


class TestManagerNeverTouchesLLM:
    """Guards against this module accidentally depending on the LLM layer."""

    def test_manager_module_does_not_import_llm_package(self) -> None:
        """app.prompting.manager's source should have no reference to app.llm.

        PromptManager is responsible only for loading and rendering
        templates; it must never import or call into the LLM layer.
        """
        import inspect

        import app.prompting.manager as manager_module

        source = inspect.getsource(manager_module)

        assert "app.llm" not in source
        assert "OllamaClient" not in source
        assert "BaseLLM" not in source
