"""Shared message contract.

:class:`Message` is the strongly typed unit of communication that
every future module (agents, orchestration, API) must use instead of
passing raw strings or dictionaries between components. This module
defines the contract only — no messaging, routing, or delivery logic
belongs here.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from app.schemas.enums import MessageType


class Message(BaseModel):
    """A single, strongly typed message exchanged between two parties.

    Attributes:
        id: Unique identifier for this message, generated
            automatically if not supplied.
        sender: Identifier of the message's originator (e.g. an agent
            name or role).
        receiver: Identifier of the message's intended recipient.
        content: The message body.
        message_type: Category of the message. Defaults to
            :attr:`MessageType.REQUEST`.
        timestamp: UTC time the message was created, generated
            automatically if not supplied.
    """

    id: UUID = Field(default_factory=uuid4)
    sender: str
    receiver: str
    content: str
    message_type: MessageType = Field(default=MessageType.REQUEST)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("sender", "receiver", "content")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        """Ensure required text fields are not empty or whitespace-only.

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
