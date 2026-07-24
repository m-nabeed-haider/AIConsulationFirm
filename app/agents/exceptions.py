"""Custom exceptions for the base agent framework.

All errors raised by :mod:`app.agents` are instances of
:class:`AgentError` (or one of its subclasses). Callers should catch
:class:`AgentError` when they do not need to distinguish between
failure modes.
"""


class AgentError(Exception):
    """Base exception for all errors raised by the agent framework.

    Every other exception in :mod:`app.agents` inherits from this
    class, allowing callers to catch a single exception type when they
    do not need to distinguish between failure modes. It is also
    raised directly for registry-level errors (e.g. duplicate or
    missing agent registration).
    """


class InvalidTaskError(AgentError):
    """Raised when a task cannot be processed by an agent.

    This covers both structural problems (e.g. the object passed to
    :meth:`app.agents.base.BaseAgent.execute` is not a
    :class:`app.schemas.task.Task`) and lifecycle problems (e.g. the
    task's status makes it ineligible for execution, such as a task
    that has already completed or been cancelled).
    """


class AgentExecutionError(AgentError):
    """Raised when an agent fails while executing a valid task.

    This wraps failures from the subsystems an agent orchestrates —
    prompt loading/rendering (:mod:`app.prompting`) and LLM generation
    (:mod:`app.llm`) — into a single, agent-layer exception, so callers
    do not need to know which underlying subsystem failed.
    """
