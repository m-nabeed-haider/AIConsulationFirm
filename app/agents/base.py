"""Reusable base class for every AI agent in the platform.

:class:`BaseAgent` orchestrates the modules built in Modules 1-4 —
:class:`app.llm.base.BaseLLM` and
:class:`app.prompting.manager.PromptManager` — into a single, fixed
execution lifecycle: receive a task, validate it, render a prompt,
call the LLM, and return a message. It contains no business-specific
logic of its own; future agents (``ResearchAgent``, ``PlannerAgent``,
``ReviewerAgent``, ``WriterAgent``, ...) inherit from this class and
customize only how a task is turned into prompt template variables.
"""

from typing import Any

from app.agents.context import AgentContext
from app.agents.exceptions import AgentExecutionError, InvalidTaskError
from app.core.logger import logger
from app.llm.base import BaseLLM
from app.llm.exceptions import LLMError
from app.llm.response import LLMResponse
from app.prompting.exceptions import PromptError
from app.prompting.manager import PromptManager
from app.schemas.agent import AgentInfo
from app.schemas.enums import MessageType, TaskStatus
from app.schemas.message import Message
from app.schemas.task import Task

_DEFAULT_RECEIVER: str = "caller"

_EXECUTABLE_TASK_STATUSES: frozenset[TaskStatus] = frozenset(
    {TaskStatus.PENDING, TaskStatus.IN_PROGRESS}
)


class BaseAgent:
    """Reusable orchestration base class for every AI agent.

    ``BaseAgent`` is responsible only for *orchestrating* existing
    modules — it validates a :class:`Task`, renders a prompt via an
    injected :class:`PromptManager`, calls an injected
    :class:`BaseLLM`, and returns the result as a :class:`Message`. It
    never constructs its own :class:`PromptManager` or :class:`BaseLLM`;
    both are supplied by the caller (dependency injection), keeping
    ``BaseAgent`` fully decoupled from any specific LLM provider or
    prompt-loading configuration.

    Subclasses customize agent-specific behavior by overriding
    :meth:`build_prompt_context` (required for anything beyond the
    generic default) and, optionally, :meth:`validate_task` for
    additional task validation. No other method needs to be
    overridden to add a new agent.
    """

    def __init__(
        self,
        metadata: AgentInfo,
        llm: BaseLLM,
        prompt_manager: PromptManager,
        prompt_template: str,
    ) -> None:
        """Initialize the agent.

        Args:
            metadata: Identity of this agent (name, role, description).
            llm: The language model this agent uses to generate
                responses. Injected by the caller; never constructed
                internally.
            prompt_manager: The prompt manager used to load and render
                this agent's prompt template. Injected by the caller;
                never constructed internally.
            prompt_template: Name of the prompt template this agent
                renders on each execution (e.g. ``"system/research"``),
                as understood by ``prompt_manager``.
        """
        self.metadata = metadata
        self._llm = llm
        self._prompt_manager = prompt_manager
        self._prompt_template = prompt_template

    def execute(
        self,
        task: Task,
        context: AgentContext | None = None,
        receiver: str = _DEFAULT_RECEIVER,
    ) -> Message:
        """Run this agent's fixed execution lifecycle against a task.

        The lifecycle is: validate the task, build the prompt
        rendering context, render the configured prompt template, call
        the injected LLM, and return the result as a :class:`Message`.

        Args:
            task: The unit of work for this agent to process.
            context: Lightweight, transient execution context (not
                memory). Defaults to a freshly generated
                :class:`AgentContext` if not supplied.
            receiver: Identifier of the intended recipient of the
                resulting message (e.g. a future supervisor). Defaults
                to ``"caller"``, since multi-agent communication is
                out of scope for this module.

        Returns:
            Message: The agent's response, with ``sender`` set to this
            agent's name and ``content`` set to the LLM's generated
            text.

        Raises:
            InvalidTaskError: If ``task`` is not a valid, executable
                :class:`Task`.
            AgentExecutionError: If prompt rendering or LLM generation
                fails.
        """
        self.validate_task(task)
        resolved_context = context or AgentContext()

        logger.info(
            "Agent '{}' starting execution (task_id={}, execution_id={}).",
            self.metadata.name,
            task.id,
            resolved_context.execution_id,
        )

        prompt_context = self.build_prompt_context(task, resolved_context)
        rendered_prompt = self._render_prompt(prompt_context)
        llm_response = self._generate(rendered_prompt)

        message = Message(
            sender=self.metadata.name,
            receiver=receiver,
            content=llm_response.text,
            message_type=MessageType.RESPONSE,
        )

        logger.info(
            "Agent '{}' completed execution (task_id={}, execution_id={}, "
            "duration={:.3f}s).",
            self.metadata.name,
            task.id,
            resolved_context.execution_id,
            llm_response.duration,
        )

        return message

    def validate_task(self, task: Task) -> None:
        """Validate that a task is well-formed and eligible for execution.

        The default implementation checks only structural and
        lifecycle validity — that ``task`` is actually a
        :class:`Task`, and that its status permits execution (
        :attr:`TaskStatus.PENDING` or :attr:`TaskStatus.IN_PROGRESS`).
        Subclasses may override this to add agent-specific validation,
        calling ``super().validate_task(task)`` first.

        Args:
            task: The task to validate.

        Raises:
            InvalidTaskError: If ``task`` is not a :class:`Task`
                instance, or its status is not eligible for execution.
        """
        if not isinstance(task, Task):
            raise InvalidTaskError(
                f"Expected a Task instance, got {type(task).__name__!r}."
            )

        if task.status not in _EXECUTABLE_TASK_STATUSES:
            raise InvalidTaskError(
                f"Task '{task.id}' has status '{task.status.value}' and cannot "
                f"be executed. Eligible statuses are: "
                f"{sorted(status.value for status in _EXECUTABLE_TASK_STATUSES)}."
            )

    def build_prompt_context(self, task: Task, context: AgentContext) -> dict[str, Any]:
        """Build the variable context used to render this agent's prompt template.

        The default implementation exposes only the task's own fields
        as generic variables, with no assumptions about any specific
        agent's template. Subclasses represent a specific role
        (research, planning, review, ...) and should override this
        method to map ``task`` (and, if useful, ``context``) onto the
        variable names their specific prompt template expects.

        Args:
            task: The task being executed.
            context: The execution context for this run.

        Returns:
            dict[str, Any]: Variables to pass to
            :meth:`app.prompting.manager.PromptManager.render`.
        """
        return {
            "task_title": task.title,
            "task_description": task.description,
        }

    def _render_prompt(self, prompt_context: dict[str, Any]) -> str:
        """Render this agent's configured prompt template.

        Args:
            prompt_context: Variables to render the template with.

        Returns:
            str: The rendered prompt text.

        Raises:
            AgentExecutionError: If the template cannot be loaded or
                rendered.
        """
        try:
            return self._prompt_manager.render(self._prompt_template, prompt_context)
        except PromptError as exc:
            logger.error(
                "Agent '{}' failed to render prompt template '{}': {}.",
                self.metadata.name,
                self._prompt_template,
                exc,
            )
            raise AgentExecutionError(
                f"Agent '{self.metadata.name}' failed to render prompt "
                f"template '{self._prompt_template}': {exc}"
            ) from exc

    def _generate(self, prompt: str) -> LLMResponse:
        """Invoke the injected LLM with a rendered prompt.

        Args:
            prompt: The fully rendered prompt text.

        Returns:
            LLMResponse: The LLM's generated response.

        Raises:
            AgentExecutionError: If LLM generation fails.
        """
        try:
            return self._llm.generate(prompt)
        except LLMError as exc:
            logger.error(
                "Agent '{}' failed during LLM generation: {}.",
                self.metadata.name,
                exc,
            )
            raise AgentExecutionError(
                f"Agent '{self.metadata.name}' failed during LLM generation: {exc}"
            ) from exc
