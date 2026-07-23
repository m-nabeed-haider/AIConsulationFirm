"""Unit tests for :mod:`app.schemas.enums`."""

import pytest

from app.schemas.enums import AgentRole, MessageType, TaskPriority, TaskStatus


class TestTaskStatus:
    """Tests for the TaskStatus enum."""

    def test_expected_members_exist(self) -> None:
        """All expected lifecycle states should be defined."""
        assert {member.value for member in TaskStatus} == {
            "pending",
            "in_progress",
            "completed",
            "failed",
            "cancelled",
        }

    def test_is_string_subclass(self) -> None:
        """Members should behave as plain strings for serialization."""
        assert isinstance(TaskStatus.PENDING, str)
        assert TaskStatus.PENDING == "pending"

    def test_invalid_value_raises(self) -> None:
        """Constructing from an unrecognized value should raise ValueError."""
        with pytest.raises(ValueError):
            TaskStatus("not_a_real_status")


class TestTaskPriority:
    """Tests for the TaskPriority enum."""

    def test_expected_members_exist(self) -> None:
        """All expected priority levels should be defined."""
        assert {member.value for member in TaskPriority} == {
            "low",
            "medium",
            "high",
            "critical",
        }

    def test_is_string_subclass(self) -> None:
        """Members should behave as plain strings for serialization."""
        assert isinstance(TaskPriority.HIGH, str)
        assert TaskPriority.HIGH == "high"

    def test_invalid_value_raises(self) -> None:
        """Constructing from an unrecognized value should raise ValueError."""
        with pytest.raises(ValueError):
            TaskPriority("urgent")


class TestMessageType:
    """Tests for the MessageType enum."""

    def test_expected_members_exist(self) -> None:
        """All expected message categories should be defined."""
        assert {member.value for member in MessageType} == {
            "request",
            "response",
            "notification",
            "error",
            "system",
        }

    def test_is_string_subclass(self) -> None:
        """Members should behave as plain strings for serialization."""
        assert isinstance(MessageType.ERROR, str)
        assert MessageType.ERROR == "error"

    def test_invalid_value_raises(self) -> None:
        """Constructing from an unrecognized value should raise ValueError."""
        with pytest.raises(ValueError):
            MessageType("broadcast")


class TestAgentRole:
    """Tests for the AgentRole enum."""

    def test_expected_members_exist(self) -> None:
        """All expected agent roles should be defined."""
        assert {member.value for member in AgentRole} == {
            "supervisor",
            "project_manager",
            "research_analyst",
            "business_analyst",
            "technical_architect",
            "financial_analyst",
            "software_engineer",
            "documentation_writer",
            "reviewer",
            "evaluator",
        }

    def test_is_string_subclass(self) -> None:
        """Members should behave as plain strings for serialization."""
        assert isinstance(AgentRole.SUPERVISOR, str)
        assert AgentRole.SUPERVISOR == "supervisor"

    def test_invalid_value_raises(self) -> None:
        """Constructing from an unrecognized value should raise ValueError."""
        with pytest.raises(ValueError):
            AgentRole("ceo")
