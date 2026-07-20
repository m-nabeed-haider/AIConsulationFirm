"""Unit tests for :class:`app.llm.providers.ollama.OllamaProvider`.

``OllamaClient`` is fully mocked in every test here (via
``unittest.mock.MagicMock``, configured to match the client's public
interface), so nothing in this module requires a running Ollama
instance or performs real network I/O.
"""

from unittest.mock import MagicMock

import pytest

from app.llm.client import OllamaClient
from app.llm.exceptions import LLMError, OllamaConnectionError
from app.llm.models import GenerationResult, HealthStatus, ModelInfo, ModelList
from app.llm.providers.ollama import OllamaProvider
from app.llm.response import LLMResponse


def make_mock_client() -> MagicMock:
    """Create a mock that mirrors the public interface of OllamaClient.

    Returns:
        MagicMock: A mock spec'd against :class:`OllamaClient`, so
        calling an undefined method raises ``AttributeError`` just
        like the real client would.
    """
    return MagicMock(spec=OllamaClient)


class TestGenerateDelegation:
    """Tests that generate() correctly delegates to OllamaClient.generate()."""

    def test_delegates_prompt_to_client(self) -> None:
        """The prompt should be forwarded to the underlying client unchanged."""
        mock_client = make_mock_client()
        mock_client.generate.return_value = GenerationResult(
            model="llama3", response="Hello!", done=True
        )
        provider = OllamaProvider(client=mock_client)

        provider.generate("Say hello")

        mock_client.generate.assert_called_once_with(prompt="Say hello")

    def test_returns_llm_response_built_from_client_result(self) -> None:
        """The client's GenerationResult should be adapted into an LLMResponse."""
        mock_client = make_mock_client()
        mock_client.generate.return_value = GenerationResult(
            model="llama3", response="Hello!", done=True
        )
        provider = OllamaProvider(client=mock_client)

        result = provider.generate("Say hello")

        assert isinstance(result, LLMResponse)
        assert result.text == "Hello!"
        assert result.model == "llama3"
        assert result.duration >= 0

    def test_propagates_exceptions_from_client_unchanged(self) -> None:
        """Exceptions raised by the client must propagate without being swallowed."""
        mock_client = make_mock_client()
        mock_client.generate.side_effect = OllamaConnectionError("unreachable")
        provider = OllamaProvider(client=mock_client)

        with pytest.raises(OllamaConnectionError):
            provider.generate("Say hello")

    def test_propagates_generic_llm_error(self) -> None:
        """A generic LLMError from the client should also propagate unchanged."""
        mock_client = make_mock_client()
        mock_client.generate.side_effect = LLMError("unexpected failure")
        provider = OllamaProvider(client=mock_client)

        with pytest.raises(LLMError):
            provider.generate("Say hello")


class TestHealthCheckDelegation:
    """Tests that health_check() correctly delegates to OllamaClient."""

    def test_delegates_to_client_and_returns_result(self) -> None:
        """health_check() should return exactly what the client returns."""
        mock_client = make_mock_client()
        expected = HealthStatus(
            is_available=True, message="Ollama server is available."
        )
        mock_client.health_check.return_value = expected
        provider = OllamaProvider(client=mock_client)

        result = provider.health_check()

        mock_client.health_check.assert_called_once_with()
        assert result == expected


class TestListModelsDelegation:
    """Tests that list_models() correctly delegates to OllamaClient."""

    def test_delegates_to_client_and_returns_result(self) -> None:
        """list_models() should return exactly what the client returns."""
        mock_client = make_mock_client()
        expected = ModelList(models=[ModelInfo(name="llama3")])
        mock_client.list_models.return_value = expected
        provider = OllamaProvider(client=mock_client)

        result = provider.list_models()

        mock_client.list_models.assert_called_once_with()
        assert result == expected

    def test_propagates_exceptions_from_client_unchanged(self) -> None:
        """Exceptions raised by the client must propagate without being swallowed."""
        mock_client = make_mock_client()
        mock_client.list_models.side_effect = OllamaConnectionError("unreachable")
        provider = OllamaProvider(client=mock_client)

        with pytest.raises(OllamaConnectionError):
            provider.list_models()


class TestProviderIsBaseLLM:
    """Tests that OllamaProvider genuinely satisfies the BaseLLM contract."""

    def test_provider_can_be_used_as_base_llm(self) -> None:
        """OllamaProvider should be a valid, concrete BaseLLM implementation."""
        from app.llm.base import BaseLLM

        mock_client = make_mock_client()
        provider: BaseLLM = OllamaProvider(client=mock_client)

        assert isinstance(provider, BaseLLM)
