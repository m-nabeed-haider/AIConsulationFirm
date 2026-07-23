"""Unit tests for :class:`app.schemas.agent.AgentInfo`."""

from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.agent import AgentInfo
from app.schemas.enums import AgentRole


class TestDefaultsAndGeneration:
    """Tests for auto-generated fields and default values."""

    def test_id_is_auto_generated_uuid(self) -> None:
        """id should default to an auto-generated UUID."""
        agent = AgentInfo(name="Ava", role=AgentRole.SUPERVISOR)

        assert isinstance(agent.id, UUID)

    def test_ids_are_unique_across_instances(self) -> None:
        """Two agents constructed without an explicit id should differ."""
        first = AgentInfo(name="Ava", role=AgentRole.SUPERVISOR)
        second = AgentInfo(name="Bo", role=AgentRole.REVIEWER)

        assert first.id != second.id

    def test_description_defaults_to_empty_string(self) -> None:
        """description should default to an empty string when omitted."""
        agent = AgentInfo(name="Ava", role=AgentRole.SUPERVISOR)

        assert agent.description == ""


class TestValidation:
    """Tests for field validation and rejection of invalid values."""

    def test_valid_agent_constructs_successfully(self) -> None:
        """Providing all fields explicitly should construct a valid agent."""
        agent = AgentInfo(
            name="Ava",
            role=AgentRole.PROJECT_MANAGER,
            description="Coordinates tasks across the team.",
        )

        assert agent.name == "Ava"
        assert agent.role == AgentRole.PROJECT_MANAGER

    def test_missing_required_fields_raise(self) -> None:
        """Omitting required fields should raise a validation error."""
        with pytest.raises(ValidationError):
            AgentInfo()  # type: ignore[call-arg]

    def test_blank_name_raises(self) -> None:
        """A whitespace-only name should be rejected."""
        with pytest.raises(ValidationError):
            AgentInfo(name="   ", role=AgentRole.SUPERVISOR)

    def test_name_is_stripped(self) -> None:
        """Leading/trailing whitespace should be stripped from the name."""
        agent = AgentInfo(name="  Ava  ", role=AgentRole.SUPERVISOR)

        assert agent.name == "Ava"

    def test_invalid_role_raises(self) -> None:
        """An unrecognized role value should raise a validation error."""
        with pytest.raises(ValidationError):
            AgentInfo(name="Ava", role="ceo")  # type: ignore[arg-type]

    def test_invalid_id_raises(self) -> None:
        """A non-UUID id value should raise a validation error."""
        with pytest.raises(ValidationError):
            AgentInfo(
                id="not-a-uuid",  # type: ignore[arg-type]
                name="Ava",
                role=AgentRole.SUPERVISOR,
            )


class TestSerialization:
    """Tests for round-tripping AgentInfo through dict/JSON representations."""

    def test_model_dump_round_trip(self) -> None:
        """An agent should survive a model_dump() -> model_validate() round trip."""
        original = AgentInfo(name="Ava", role=AgentRole.TECHNICAL_ARCHITECT)

        dumped = original.model_dump()
        restored = AgentInfo.model_validate(dumped)

        assert restored == original

    def test_model_dump_json_round_trip(self) -> None:
        """An agent should survive a model_dump_json() -> model_validate_json() round trip."""
        original = AgentInfo(name="Ava", role=AgentRole.EVALUATOR)

        json_str = original.model_dump_json()
        restored = AgentInfo.model_validate_json(json_str)

        assert restored == original

    def test_role_serializes_to_plain_string(self) -> None:
        """role should serialize as its plain string value, not an enum repr."""
        agent = AgentInfo(name="Ava", role=AgentRole.FINANCIAL_ANALYST)

        dumped = agent.model_dump(mode="json")

        assert dumped["role"] == "financial_analyst"
