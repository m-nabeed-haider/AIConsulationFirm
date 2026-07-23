"""Unit tests for :class:`app.schemas.message.Message`."""

import json
from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.enums import MessageType
from app.schemas.message import Message


class TestDefaultsAndGeneration:
    """Tests for auto-generated fields and default values."""

    def test_id_is_auto_generated_uuid(self) -> None:
        """id should default to an auto-generated UUID."""
        message = Message(sender="agent-a", receiver="agent-b", content="hello")

        assert isinstance(message.id, UUID)

    def test_ids_are_unique_across_instances(self) -> None:
        """Two messages constructed without an explicit id should differ."""
        first = Message(sender="a", receiver="b", content="hi")
        second = Message(sender="a", receiver="b", content="hi")

        assert first.id != second.id

    def test_timestamp_is_auto_generated(self) -> None:
        """timestamp should default to the current UTC time."""
        message = Message(sender="a", receiver="b", content="hi")

        assert isinstance(message.timestamp, datetime)

    def test_message_type_defaults_to_request(self) -> None:
        """message_type should default to MessageType.REQUEST."""
        message = Message(sender="a", receiver="b", content="hi")

        assert message.message_type == MessageType.REQUEST


class TestValidation:
    """Tests for field validation and rejection of invalid values."""

    def test_valid_message_constructs_successfully(self) -> None:
        """Providing all required fields should construct a valid message."""
        message = Message(
            sender="supervisor",
            receiver="research_analyst",
            content="Please begin market research.",
            message_type=MessageType.REQUEST,
        )

        assert message.sender == "supervisor"
        assert message.receiver == "research_analyst"
        assert message.content == "Please begin market research."

    def test_missing_required_field_raises(self) -> None:
        """Omitting a required field should raise a validation error."""
        with pytest.raises(ValidationError):
            Message(sender="a", receiver="b")  # type: ignore[call-arg]

    @pytest.mark.parametrize("field_name", ["sender", "receiver", "content"])
    def test_blank_required_text_field_raises(self, field_name: str) -> None:
        """An empty or whitespace-only required text field should be rejected."""
        valid_fields = {"sender": "a", "receiver": "b", "content": "hi"}
        valid_fields[field_name] = "   "

        with pytest.raises(ValidationError):
            Message(**valid_fields)

    def test_text_fields_are_stripped(self) -> None:
        """Leading/trailing whitespace should be stripped from text fields."""
        message = Message(sender="  a  ", receiver="b", content="  hello  ")

        assert message.sender == "a"
        assert message.content == "hello"

    def test_invalid_message_type_raises(self) -> None:
        """An unrecognized message_type value should raise a validation error."""
        with pytest.raises(ValidationError):
            Message(
                sender="a",
                receiver="b",
                content="hi",
                message_type="not_a_real_type",  # type: ignore[arg-type]
            )

    def test_invalid_id_raises(self) -> None:
        """A non-UUID id value should raise a validation error."""
        with pytest.raises(ValidationError):
            Message(
                id="not-a-uuid",  # type: ignore[arg-type]
                sender="a",
                receiver="b",
                content="hi",
            )


class TestSerialization:
    """Tests for round-tripping Message through dict/JSON representations."""

    def test_model_dump_round_trip(self) -> None:
        """A message should survive a model_dump() -> model_validate() round trip."""
        original = Message(sender="a", receiver="b", content="hi")

        dumped = original.model_dump()
        restored = Message.model_validate(dumped)

        assert restored == original

    def test_model_dump_json_round_trip(self) -> None:
        """A message should survive a model_dump_json() -> model_validate_json() round trip."""
        original = Message(sender="a", receiver="b", content="hi")

        json_str = original.model_dump_json()
        restored = Message.model_validate_json(json_str)

        assert restored == original
        # Confirm it is actually valid, parseable JSON.
        assert json.loads(json_str)["sender"] == "a"

    def test_message_type_serializes_to_plain_string(self) -> None:
        """message_type should serialize as its plain string value, not an enum repr."""
        message = Message(
            sender="a", receiver="b", content="hi", message_type=MessageType.ERROR
        )

        dumped = message.model_dump(mode="json")

        assert dumped["message_type"] == "error"
