"""Ollama implementation of the BaseLLM contract.

:class:`OllamaProvider` adapts the existing
:class:`app.llm.client.OllamaClient` (Module 1) to the
provider-agnostic :class:`app.llm.base.BaseLLM` interface. It contains
no HTTP logic of its own — every request is delegated to the injected
``OllamaClient``, and any failure it raises propagates unchanged.
"""

import time

from app.core.logger import logger
from app.llm.base import BaseLLM
from app.llm.client import OllamaClient
from app.llm.models import HealthStatus, ModelList
from app.llm.response import LLMResponse

_PROVIDER_NAME: str = "ollama"


class OllamaProvider(BaseLLM):
    """BaseLLM implementation backed by a local Ollama server.

    This class is a thin adapter: all HTTP communication, timeout
    handling, and error translation is already handled by
    :class:`app.llm.client.OllamaClient`. This provider is responsible
    only for satisfying the ``BaseLLM`` contract and shaping responses
    into provider-agnostic models.
    """

    def __init__(self, client: OllamaClient | None = None) -> None:
        """Initialize the provider.

        Args:
            client: The :class:`OllamaClient` to delegate all
                communication to. Defaults to a new client built from
                application settings. Primarily overridden in tests
                to inject a mock client.
        """
        self._client = client or OllamaClient()

    def generate(self, prompt: str) -> LLMResponse:
        """Generate a text completion by delegating to ``OllamaClient``.

        Args:
            prompt: The input prompt to send to the model.

        Returns:
            LLMResponse: The generated text and associated metadata.

        Raises:
            app.llm.exceptions.LLMError: Propagated unchanged if the
                underlying client fails (e.g. connection error,
                timeout, or unknown model).
        """
        start_time = time.perf_counter()

        try:
            result = self._client.generate(prompt=prompt)
        except Exception:
            duration = time.perf_counter() - start_time
            logger.error(
                "LLM generation failed (provider='{}', duration={:.3f}s).",
                _PROVIDER_NAME,
                duration,
            )
            raise

        duration = time.perf_counter() - start_time
        logger.info(
            "LLM generation succeeded (provider='{}', model='{}', duration={:.3f}s).",
            _PROVIDER_NAME,
            result.model,
            duration,
        )

        return LLMResponse(
            text=result.response,
            model=result.model,
            duration=duration,
        )

    def health_check(self) -> HealthStatus:
        """Check Ollama server availability by delegating to ``OllamaClient``.

        Returns:
            HealthStatus: The outcome of the connectivity check.
        """
        return self._client.health_check()

    def list_models(self) -> ModelList:
        """List available models by delegating to ``OllamaClient``.

        Returns:
            ModelList: The models currently available on the server.

        Raises:
            app.llm.exceptions.LLMError: Propagated unchanged if the
                underlying client fails.
        """
        return self._client.list_models()
