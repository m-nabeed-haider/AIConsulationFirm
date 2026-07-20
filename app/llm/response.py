"""Provider-agnostic response model for the LLM abstraction layer.

:class:`LLMResponse` is what every :class:`app.llm.base.BaseLLM`
implementation returns from ``generate()``. It intentionally does not
mirror any specific provider's raw API response shape, so that
callers (and future agents) never depend on provider-specific fields.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """Result of a single text-generation call, independent of provider.

    Attributes:
        text: The generated text.
        model: Name of the model that produced the response.
        duration: Wall-clock time, in seconds, the generation took.
        created_at: UTC timestamp of when this response was created.
        metadata: Open-ended extension point for additional,
            provider-specific, or future data (e.g. token counts,
            finish reason) that should not require changing this
            model's core fields.
    """

    text: str
    model: str
    duration: float = Field(ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)