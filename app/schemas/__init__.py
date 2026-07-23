"""Shared data models package.

This package defines the strongly typed domain contracts shared
across the entire application: :class:`app.schemas.message.Message`,
:class:`app.schemas.task.Task`, and
:class:`app.schemas.agent.AgentInfo`, along with the enums that back
their constrained fields.

Every future module — agents, planners, supervisors, workflows, and
APIs — must communicate using these models rather than raw
dictionaries or strings. This package defines the contracts only; it
contains no AI logic, persistence, or business behavior.
"""

from app.schemas.agent import AgentInfo
from app.schemas.enums import AgentRole, MessageType, TaskPriority, TaskStatus
from app.schemas.message import Message
from app.schemas.task import Task

__all__ = [
    "AgentInfo",
    "Message",
    "Task",
    "AgentRole",
    "MessageType",
    "TaskPriority",
    "TaskStatus",
]
