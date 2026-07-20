"""LLM integration package.

This package provides the application's LLM abstraction layer.

Application code and future agents should depend on
:class:`app.llm.base.BaseLLM`, obtained via
:class:`app.llm.factory.LLMFactory`, rather than on any concrete
provider or on :class:`app.llm.client.OllamaClient` directly:

    from app.llm import LLMFactory

    llm = LLMFactory.create()
    response = llm.generate("Explain recursion in one sentence.")

The lower-level :class:`OllamaClient` (Module 1) remains available for
provider implementations to build on, but is no longer the intended
entry point for application code.
"""

from app.llm.base import BaseLLM
from app.llm.client import OllamaClient
from app.llm.exceptions import (
    LLMError,
    ModelNotFoundError,
    OllamaConnectionError,
    OllamaTimeoutError,
)
from app.llm.factory import LLMFactory
from app.llm.models import GenerationResult, HealthStatus, ModelInfo, ModelList
from app.llm.providers.ollama import OllamaProvider
from app.llm.response import LLMResponse

__all__ = [
    # Abstraction layer (Module 2)
    "BaseLLM",
    "LLMFactory",
    "LLMResponse",
    "OllamaProvider",
    # Ollama client (Module 1)
    "OllamaClient",
    "LLMError",
    "ModelNotFoundError",
    "OllamaConnectionError",
    "OllamaTimeoutError",
    "GenerationResult",
    "HealthStatus",
    "ModelInfo",
    "ModelList",
]
