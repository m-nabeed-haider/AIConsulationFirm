"""Abstract contract for LLM providers.

:class:`BaseLLM` is the interface all application code — and, in
future modules, all agents — must depend on when they need to talk to
a language model. No caller should import or instantiate a concrete
provider (e.g. ``OllamaProvider``) directly; instead, an instance
should be obtained through :class:`app.llm.factory.LLMFactory`.

This module contains no implementation, only the contract.
"""

from abc import ABC, abstractmethod

from app.llm.models import HealthStatus, ModelList
from app.llm.response import LLMResponse


class BaseLLM(ABC):
    """Abstract base class defining the contract every LLM provider must satisfy.

    Concrete subclasses are responsible for adapting a specific
    backend (e.g. Ollama, and in future modules OpenAI, Anthropic,
    Gemini, or vLLM) to this provider-agnostic interface.
    """

    @abstractmethod
    def generate(self, prompt: str) -> LLMResponse:
        """Generate a text completion for the given prompt.

        Args:
            prompt: The input prompt to send to the underlying model.

        Returns:
            LLMResponse: The generated text and associated metadata.
        """
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> HealthStatus:
        """Check whether the underlying LLM provider is reachable.

        Returns:
            HealthStatus: The outcome of the connectivity check.
        """
        raise NotImplementedError

    @abstractmethod
    def list_models(self) -> ModelList:
        """Retrieve the models available from the underlying provider.

        Returns:
            ModelList: The models currently available.
        """
        raise NotImplementedError
