"""Shared task contract.

:class:`Task` is the strongly typed unit of work that every future
module (planners, supervisors, workflows, API) must use to represent
a unit of work, instead of passing dictionaries or raw strings. This
module defines the contract only — no scheduling, execution, or
business logic belongs here.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from app.schemas.enums import TaskPriority, TaskStatus


class Task(BaseModel):
    """A single, strongly typed unit of work.

    Attributes:
        id: Unique identifier for this task, generated automatically
            if not supplied.
        title: Short, human-readable summary of the task.
        description: Detailed description of what the task involves.
        priority: Relative priority of the task. Defaults to
            :attr:`TaskPriority.MEDIUM`.
        status: Current lifecycle status of the task. Defaults to
            :attr:`TaskStatus.PENDING`.
        created_at: UTC time the task was created, generated
            automatically if not supplied.
        updated_at: UTC time the task was last updated, generated
            automatically if not supplied. Callers are responsible for
            setting this explicitly when modifying a task; this model
            does not update it automatically.
    """

    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str = Field(default="")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        """Ensure the task title is not empty or whitespace-only.

        Args:
            value: The raw field value provided to the model.

        Returns:
            str: The value, stripped of leading/trailing whitespace.

        Raises:
            ValueError: If the value is empty after stripping.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty or whitespace-only")
        return stripped
