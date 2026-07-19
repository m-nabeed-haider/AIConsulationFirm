"""Data models for the Ollama client.

This module defines the typed objects returned by
:class:`app.llm.client.OllamaClient`. Using dedicated models — rather
than returning raw dictionaries parsed from HTTP responses — keeps the
shape of Ollama's REST API from leaking into the rest of the
application.
"""

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """Result of a connectivity check against the Ollama server.

    Attributes:
        is_available: Whether the Ollama server responded
            successfully.
        message: Human-readable description of the health check
            result.
    """

    is_available: bool
    message: str


class ModelInfo(BaseModel):
    """Metadata describing a single model available on the Ollama server.

    Attributes:
        name: The model's identifier (e.g. ``"llama3"``).
        size: The model's size on disk, in bytes, if reported by the
            server.
        digest: Content digest/hash identifying the model version, if
            reported by the server.
    """

    name: str
    size: int | None = None
    digest: str | None = None


class ModelList(BaseModel):
    """Collection of models available on the Ollama server.

    Attributes:
        models: The list of available models.
    """

    models: list[ModelInfo] = Field(default_factory=list)


class GenerationResult(BaseModel):
    """Result of a single text-generation request.

    Attributes:
        model: Name of the model that produced the response.
        response: The generated text.
        done: Whether the server reported the generation as complete.
    """

    model: str
    response: str
    done: bool = True
