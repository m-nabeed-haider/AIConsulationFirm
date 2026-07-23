"""Prompt management subsystem.

This package separates prompt engineering from application logic.
Prompt templates live as external Markdown (``.md``) files under the
project's ``prompts/`` directory — never embedded as strings in Python
source. :class:`app.prompting.manager.PromptManager` is the public
entry point for loading and rendering them:

    from app.prompting import PromptManager

    prompts = PromptManager()
    rendered = prompts.render("system/research", {"topic": "local LLMs"})

This subsystem never communicates with an LLM; it is responsible only
for turning a template name and a context into rendered text.
"""

from app.prompting.exceptions import (
    PromptError,
    PromptNotFoundError,
    PromptRenderingError,
)
from app.prompting.loader import PromptLoader
from app.prompting.manager import PromptManager
from app.prompting.renderer import PromptRenderer

__all__ = [
    "PromptManager",
    "PromptLoader",
    "PromptRenderer",
    "PromptError",
    "PromptNotFoundError",
    "PromptRenderingError",
]
