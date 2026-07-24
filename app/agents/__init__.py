"""Base agent framework.

This package provides the reusable foundation every AI agent in the
platform builds on:

- :class:`app.agents.base.BaseAgent` — orchestrates an injected
  :class:`app.llm.base.BaseLLM` and
  :class:`app.prompting.manager.PromptManager` through a fixed
  lifecycle: validate task, render prompt, call the LLM, return a
  message.
- :class:`app.agents.context.AgentContext` — a lightweight, transient
  per-execution context (not memory).
- :class:`app.agents.registry.AgentRegistry` — tracks constructed
  agent instances by name, for future use by a Supervisor.

Concrete agents (e.g. a future ``ResearchAgent``) subclass
``BaseAgent`` and override :meth:`app.agents.base.BaseAgent.build_prompt_context`
to supply their own business logic. No such concrete agents are
implemented in this package.
"""

from app.agents.base import BaseAgent
from app.agents.context import AgentContext
from app.agents.exceptions import AgentError, AgentExecutionError, InvalidTaskError
from app.agents.registry import AgentRegistry

__all__ = [
    "BaseAgent",
    "AgentContext",
    "AgentRegistry",
    "AgentError",
    "AgentExecutionError",
    "InvalidTaskError",
]
