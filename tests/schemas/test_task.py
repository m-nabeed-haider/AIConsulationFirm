"""Unit tests for :class:`app.schemas.task.Task`."""

from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.enums import TaskPriority, TaskStatus
from app.schemas.task import Task


class TestDefaultsAndGeneration:
    """Tests for auto-generated fields and default values."""

    def test_id_is_auto_generated_uuid(self) -> None:
        """id should default to an auto-generated UUID."""
        task = Task(title="Draft proposal")

        assert isinstance(task.id, UUID)

    def test_ids_are_unique_across_instances(self) -> None:
        """Two tasks constructed without an explicit id should differ."""
        first = Task(title="Task A")
        second = Task(title="Task B")

        assert first.id != second.id

    def test_timestamps_are_auto_generated(self) -> None:
        """created_at and updated_at should default to the current UTC time."""
        task = Task(title="Draft proposal")

        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_description_defaults_to_empty_string(self) -> None:
        """description should default to an empty string when omitted."""
        task = Task(title="Draft proposal")

        assert task.description == ""

    def test_priority_defaults_to_medium(self) -> None:
        """priority should default to TaskPriority.MEDIUM."""
        task = Task(title="Draft proposal")

        assert task.priority == TaskPriority.MEDIUM

    def test_status_defaults_to_pending(self) -> None:
        """status should default to TaskStatus.PENDING."""
        task = Task(title="Draft proposal")

        assert task.status == TaskStatus.PENDING


class TestValidation:
    """Tests for field validation and rejection of invalid values."""

    def test_valid_task_constructs_successfully(self) -> None:
        """Providing all fields explicitly should construct a valid task."""
        task = Task(
            title="Draft market research",
            description="Summarize competitor landscape.",
            priority=TaskPriority.HIGH,
            status=TaskStatus.IN_PROGRESS,
        )

        assert task.title == "Draft market research"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.IN_PROGRESS

    def test_missing_title_raises(self) -> None:
        """Omitting the required title field should raise a validation error."""
        with pytest.raises(ValidationError):
            Task()  # type: ignore[call-arg]

    def test_blank_title_raises(self) -> None:
        """A whitespace-only title should be rejected."""
        with pytest.raises(ValidationError):
            Task(title="   ")

    def test_title_is_stripped(self) -> None:
        """Leading/trailing whitespace should be stripped from the title."""
        task = Task(title="  Draft proposal  ")

        assert task.title == "Draft proposal"

    def test_invalid_priority_raises(self) -> None:
        """An unrecognized priority value should raise a validation error."""
        with pytest.raises(ValidationError):
            Task(title="Draft proposal", priority="urgent")  # type: ignore[arg-type]

    def test_invalid_status_raises(self) -> None:
        """An unrecognized status value should raise a validation error."""
        with pytest.raises(ValidationError):
            Task(title="Draft proposal", status="archived")  # type: ignore[arg-type]

    def test_invalid_id_raises(self) -> None:
        """A non-UUID id value should raise a validation error."""
        with pytest.raises(ValidationError):
            Task(id="not-a-uuid", title="Draft proposal")  # type: ignore[arg-type]


class TestSerialization:
    """Tests for round-tripping Task through dict/JSON representations."""

    def test_model_dump_round_trip(self) -> None:
        """A task should survive a model_dump() -> model_validate() round trip."""
        original = Task(title="Draft proposal", priority=TaskPriority.CRITICAL)

        dumped = original.model_dump()
        restored = Task.model_validate(dumped)

        assert restored == original

    def test_model_dump_json_round_trip(self) -> None:
        """A task should survive a model_dump_json() -> model_validate_json() round trip."""
        original = Task(title="Draft proposal", status=TaskStatus.COMPLETED)

        json_str = original.model_dump_json()
        restored = Task.model_validate_json(json_str)

        assert restored == original

    def test_enum_fields_serialize_to_plain_strings(self) -> None:
        """priority and status should serialize as plain string values."""
        task = Task(
            title="Draft proposal",
            priority=TaskPriority.LOW,
            status=TaskStatus.FAILED,
        )

        dumped = task.model_dump(mode="json")

        assert dumped["priority"] == "low"
        assert dumped["status"] == "failed"
