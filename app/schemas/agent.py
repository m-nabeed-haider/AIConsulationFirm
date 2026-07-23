"""Shared agent metadata contract.

:class:`AgentInfo` describes the identity of an AI agent — who it is,
what role it plays, and what it does — as plain, strongly typed
metadata. It contains no agent behavior; actual agent implementations
belong to a future module.
"""

from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from app.schemas.enums import AgentRole


class AgentInfo(BaseModel):
    """Strongly typed metadata describing a single AI agent.

    Attributes:
        id: Unique identifier for this agent, generated automatically
            if not supplied.
        name: Human-readable name of the agent (e.g. ``"Ava"``).
        role: The agent's role within the system.
        description: Short description of the agent's responsibilities.
    """

    id: UUID = Field(default_factory=uuid4)
    name: str
    role: AgentRole
    description: str = Field(default="")

    @field_validator("name")
    @classmethod
    def _name_not_blank(cls, value: str) -> str:
        """Ensure the agent name is not empty or whitespace-only.

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
