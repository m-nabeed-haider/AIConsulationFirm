"""Lightweight per-execution context for agents.

:class:`AgentContext` carries identifiers and free-form metadata for a
single :meth:`app.agents.base.BaseAgent.execute` call. It is
intentionally minimal and **not** a memory system: nothing in this
class is persisted or retrieved across executions. Memory (short-term
or long-term recall across calls) is explicitly out of scope for this
module and belongs to a future one.
"""

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentContext(BaseModel):
    """Transient context accompanying a single agent execution.

    Attributes:
        conversation_id: Identifier correlating this execution with a
            broader conversation or session. Generated automatically
            if not supplied, so a caller not tracking conversations
            can omit it entirely.
        execution_id: Identifier for this specific execution attempt.
            Generated automatically if not supplied.
        metadata: Open-ended, caller-supplied data relevant to this
            execution (e.g. request source, trace identifiers). Not
            interpreted by :class:`app.agents.base.BaseAgent` itself.
    """

    conversation_id: UUID = Field(default_factory=uuid4)
    execution_id: UUID = Field(default_factory=uuid4)
    metadata: dict[str, Any] = Field(default_factory=dict)
