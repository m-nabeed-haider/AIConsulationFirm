"""Unit tests for :class:`app.agents.context.AgentContext`."""

from uuid import UUID

from app.agents.context import AgentContext


class TestDefaults:
    """Tests for AgentContext's default, auto-generated fields."""

    def test_conversation_id_is_auto_generated_uuid(self) -> None:
        """conversation_id should default to an auto-generated UUID."""
        context = AgentContext()

        assert isinstance(context.conversation_id, UUID)

    def test_execution_id_is_auto_generated_uuid(self) -> None:
        """execution_id should default to an auto-generated UUID."""
        context = AgentContext()

        assert isinstance(context.execution_id, UUID)

    def test_conversation_and_execution_ids_differ_by_default(self) -> None:
        """The two auto-generated identifiers should not collide."""
        context = AgentContext()

        assert context.conversation_id != context.execution_id

    def test_metadata_defaults_to_empty_dict(self) -> None:
        """metadata should default to an empty dict, not a shared mutable."""
        first = AgentContext()
        second = AgentContext()

        assert first.metadata == {}
        assert first.metadata is not second.metadata

    def test_two_contexts_get_distinct_ids(self) -> None:
        """Two independently constructed contexts should not share identifiers."""
        first = AgentContext()
        second = AgentContext()

        assert first.execution_id != second.execution_id
        assert first.conversation_id != second.conversation_id


class TestExplicitValues:
    """Tests for supplying explicit values instead of relying on defaults."""

    def test_accepts_explicit_conversation_id(self) -> None:
        """An explicitly supplied conversation_id should be preserved."""
        from uuid import uuid4

        conversation_id = uuid4()
        context = AgentContext(conversation_id=conversation_id)

        assert context.conversation_id == conversation_id

    def test_accepts_arbitrary_metadata(self) -> None:
        """metadata should accept arbitrary caller-supplied data."""
        context = AgentContext(metadata={"source": "cli", "trace_id": "abc-123"})

        assert context.metadata == {"source": "cli", "trace_id": "abc-123"}
