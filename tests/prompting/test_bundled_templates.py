"""Tests for the bundled example system prompt templates.

These verify that the example templates shipped under
``prompts/system/`` (research.md, planner.md, reviewer.md) exist and
render successfully against a representative context, using the
default, project-configured :class:`PromptManager` — no mocking.
"""

from app.prompting.manager import PromptManager


class TestBundledSystemTemplates:
    """End-to-end checks for the real templates under prompts/system/."""

    def test_default_manager_finds_bundled_templates(self) -> None:
        """The default PromptManager should discover the shipped example templates."""
        manager = PromptManager()

        templates = manager.list_templates()

        assert "system/research" in templates
        assert "system/planner" in templates
        assert "system/reviewer" in templates

    def test_research_template_renders(self) -> None:
        """The research.md template should render with a representative context."""
        manager = PromptManager()

        result = manager.render(
            "system/research",
            {
                "company_name": "AI Consulting Firm",
                "topic": "local LLM adoption",
                "focus_areas": ["cost", "privacy"],
            },
        )

        assert "local LLM adoption" in result
        assert "cost" in result

    def test_research_template_renders_without_optional_focus_areas(self) -> None:
        """focus_areas is optional; omitting it should still render successfully."""
        manager = PromptManager()

        result = manager.render(
            "system/research",
            {"company_name": "AI Consulting Firm", "topic": "local LLM adoption"},
        )

        assert "local LLM adoption" in result

    def test_planner_template_renders(self) -> None:
        """The planner.md template should render with a representative context."""
        manager = PromptManager()

        result = manager.render(
            "system/planner",
            {
                "company_name": "AI Consulting Firm",
                "idea": "Build a local RAG application",
                "constraints": ["Must run offline"],
            },
        )

        assert "Build a local RAG application" in result
        assert "Must run offline" in result

    def test_reviewer_template_renders(self) -> None:
        """The reviewer.md template should render with a representative context."""
        manager = PromptManager()

        result = manager.render(
            "system/reviewer",
            {
                "company_name": "AI Consulting Firm",
                "author": "Ada",
                "submission": "Draft technical architecture document.",
            },
        )

        assert "Ada" in result
        assert "Draft technical architecture document." in result
