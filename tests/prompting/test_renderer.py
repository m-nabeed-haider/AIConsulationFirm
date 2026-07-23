"""Unit tests for :class:`app.prompting.renderer.PromptRenderer`.

These tests exercise Jinja2 rendering directly against in-memory
template strings — no filesystem access, no Ollama, no external
service involved.
"""

import pytest

from app.prompting.exceptions import PromptRenderingError
from app.prompting.renderer import PromptRenderer


@pytest.fixture
def renderer() -> PromptRenderer:
    """Provide a fresh PromptRenderer instance for each test."""
    return PromptRenderer()


class TestRenderSuccess:
    """Tests for successful rendering."""

    def test_substitutes_simple_variable(self, renderer: PromptRenderer) -> None:
        """A simple {{ variable }} should be substituted with its value."""
        result = renderer.render("Hello, {{ name }}!", {"name": "Ada"})

        assert result == "Hello, Ada!"

    def test_renders_template_with_no_variables_and_no_context(
        self, renderer: PromptRenderer
    ) -> None:
        """A template with no variables should render unchanged with an empty context."""
        result = renderer.render("Static prompt text.")

        assert result == "Static prompt text."

    def test_renders_template_with_no_variables_and_none_context(
        self, renderer: PromptRenderer
    ) -> None:
        """Passing context=None should behave the same as an empty context."""
        result = renderer.render("Static prompt text.", None)

        assert result == "Static prompt text."

    def test_renders_conditional_blocks(self, renderer: PromptRenderer) -> None:
        """Jinja2 {% if %} blocks should be evaluated correctly."""
        template = "{% if show %}Visible{% else %}Hidden{% endif %}"

        assert renderer.render(template, {"show": True}) == "Visible"
        assert renderer.render(template, {"show": False}) == "Hidden"

    def test_renders_loop_blocks(self, renderer: PromptRenderer) -> None:
        """Jinja2 {% for %} loops should be evaluated correctly."""
        template = "{% for item in items %}{{ item }},{% endfor %}"

        result = renderer.render(template, {"items": ["a", "b", "c"]})

        assert result == "a,b,c,"

    def test_extra_unused_context_variables_are_ignored(
        self, renderer: PromptRenderer
    ) -> None:
        """Supplying more context than the template uses should not raise."""
        result = renderer.render("Hello, {{ name }}!", {"name": "Ada", "unused": 123})

        assert result == "Hello, Ada!"


class TestRenderMissingVariables:
    """Tests for strict handling of missing template variables."""

    def test_missing_variable_raises_prompt_rendering_error(
        self, renderer: PromptRenderer
    ) -> None:
        """Referencing an undefined variable should raise PromptRenderingError."""
        with pytest.raises(PromptRenderingError):
            renderer.render("Hello, {{ name }}!", {})

    def test_missing_variable_with_none_context_raises(
        self, renderer: PromptRenderer
    ) -> None:
        """A template requiring a variable should raise even with context=None."""
        with pytest.raises(PromptRenderingError):
            renderer.render("Hello, {{ name }}!")

    def test_partially_missing_variable_in_loop_raises(
        self, renderer: PromptRenderer
    ) -> None:
        """A missing variable nested inside a loop body should still raise."""
        template = "{% for item in items %}{{ missing_var }}{% endfor %}"

        with pytest.raises(PromptRenderingError):
            renderer.render(template, {"items": ["a"]})


class TestRenderMalformedTemplate:
    """Tests for malformed Jinja2 template syntax."""

    def test_unclosed_tag_raises_prompt_rendering_error(
        self, renderer: PromptRenderer
    ) -> None:
        """An unclosed {% if %} block should raise PromptRenderingError."""
        with pytest.raises(PromptRenderingError):
            renderer.render("{% if condition %}Unclosed block")

    def test_invalid_expression_syntax_raises_prompt_rendering_error(
        self, renderer: PromptRenderer
    ) -> None:
        """Invalid Jinja2 expression syntax should raise PromptRenderingError."""
        with pytest.raises(PromptRenderingError):
            renderer.render("{{ name + }}")

    def test_mismatched_block_tags_raises_prompt_rendering_error(
        self, renderer: PromptRenderer
    ) -> None:
        """Mismatched block tags (e.g. {% if %} closed with {% endfor %}) should raise."""
        with pytest.raises(PromptRenderingError):
            renderer.render("{% if condition %}text{% endfor %}", {"condition": True})
