"""Shared enumerations for the application's domain models.

These enums define the fixed sets of values used by
:mod:`app.schemas.message`, :mod:`app.schemas.task`, and
:mod:`app.schemas.agent`. They contain no behavior — only the vocabulary
that every future module (agents, orchestration, API) is expected to
communicate with instead of raw strings.

All enums subclass ``str`` in addition to ``Enum`` so that they
serialize to plain strings in JSON/dict output (e.g. via Pydantic's
``model_dump_json()``) while still being usable as regular Python
enums for comparisons and type checking.
"""

from enum import Enum


class TaskStatus(str, Enum):
    """Lifecycle status of a :class:`app.schemas.task.Task`."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Relative priority of a :class:`app.schemas.task.Task`."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MessageType(str, Enum):
    """Category of a :class:`app.schemas.message.Message`."""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    SYSTEM = "system"


class AgentRole(str, Enum):
    """Role identifier for a :class:`app.schemas.agent.AgentInfo`.

    These correspond to the specialized AI "employees" described in
    the project's long-term vision. Defining the role here does not
    imply any of these agents are implemented yet — this enum only
    establishes the shared vocabulary future modules will use.
    """

    SUPERVISOR = "supervisor"
    PROJECT_MANAGER = "project_manager"
    RESEARCH_ANALYST = "research_analyst"
    BUSINESS_ANALYST = "business_analyst"
    TECHNICAL_ARCHITECT = "technical_architect"
    FINANCIAL_ANALYST = "financial_analyst"
    SOFTWARE_ENGINEER = "software_engineer"
    DOCUMENTATION_WRITER = "documentation_writer"
    REVIEWER = "reviewer"
    EVALUATOR = "evaluator"
