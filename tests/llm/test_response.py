"""Unit tests for :class:`app.llm.response.LLMResponse`."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.llm.response import LLMResponse


def test_valid_response_constructs_successfully() -> None:
    """Providing all required fields should construct a valid response."""
    response = LLMResponse(text="Hello!", model="llama3", duration=1.23)

    assert response.text == "Hello!"
    assert response.model == "llama3"
    assert response.duration == 1.23


def test_created_at_defaults_to_current_time() -> None:
    """created_at should default to a timestamp if not explicitly provided."""
    response = LLMResponse(text="Hello!", model="llama3", duration=0.1)

    assert isinstance(response.created_at, datetime)


def test_metadata_defaults_to_empty_dict() -> None:
    """metadata should default to an empty dict, not None or a shared mutable."""
    first = LLMResponse(text="a", model="m", duration=0.1)
    second = LLMResponse(text="b", model="m", duration=0.2)

    assert first.metadata == {}
    assert first.metadata is not second.metadata  # no shared mutable default


def test_metadata_accepts_arbitrary_future_fields() -> None:
    """metadata should support arbitrary extension data without schema changes."""
    response = LLMResponse(
        text="Hello!",
        model="llama3",
        duration=0.5,
        metadata={"token_count": 42, "finish_reason": "stop"},
    )

    assert response.metadata["token_count"] == 42
    assert response.metadata["finish_reason"] == "stop"


def test_missing_required_field_raises_validation_error() -> None:
    """Omitting a required field should raise a validation error."""
    with pytest.raises(ValidationError):
        LLMResponse(model="llama3", duration=0.1)  # type: ignore[call-arg]


def test_negative_duration_raises_validation_error() -> None:
    """A negative duration is not physically valid and should be rejected."""
    with pytest.raises(ValidationError):
        LLMResponse(text="Hello!", model="llama3", duration=-1.0)
