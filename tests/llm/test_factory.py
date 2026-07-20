"""Unit tests for :class:`app.llm.factory.LLMFactory`.

Constructing a provider does not perform any network I/O (the
underlying ``OllamaClient`` only opens an HTTP client lazily), so
these tests run without a running Ollama instance.
"""

import pytest

from app.core.config import Settings
from app.llm.base import BaseLLM
from app.llm.exceptions import LLMError
from app.llm.factory import LLMFactory
from app.llm.providers.ollama import OllamaProvider


def make_settings(**overrides: object) -> Settings:
    """Build a :class:`Settings` instance for testing, with overrides.

    Args:
        **overrides: Field values to override on top of test defaults.

    Returns:
        Settings: A settings instance isolated from the real process
        environment.
    """
    defaults: dict[str, object] = {
        "ollama_host": "http://testserver",
        "default_model": "llama3",
        "request_timeout": 5.0,
        "llm_provider": "ollama",
    }
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


def test_factory_returns_ollama_provider_for_ollama() -> None:
    """LLM_PROVIDER=ollama should yield an OllamaProvider instance."""
    settings = make_settings(llm_provider="ollama")

    llm = LLMFactory.create(settings=settings)

    assert isinstance(llm, OllamaProvider)
    assert isinstance(llm, BaseLLM)


def test_factory_result_satisfies_base_llm_contract() -> None:
    """The object returned by the factory must be usable as a BaseLLM."""
    settings = make_settings(llm_provider="ollama")

    llm = LLMFactory.create(settings=settings)

    assert hasattr(llm, "generate")
    assert hasattr(llm, "health_check")
    assert hasattr(llm, "list_models")


def test_factory_is_case_insensitive() -> None:
    """Provider names should be matched case-insensitively."""
    settings = make_settings(llm_provider="OLLAMA")

    llm = LLMFactory.create(settings=settings)

    assert isinstance(llm, OllamaProvider)


def test_factory_raises_llm_error_for_unsupported_provider() -> None:
    """An unrecognized provider name should raise LLMError."""
    settings = make_settings(llm_provider="openai")

    with pytest.raises(LLMError):
        LLMFactory.create(settings=settings)


def test_factory_error_message_lists_supported_providers() -> None:
    """The raised error should be informative about what is supported."""
    settings = make_settings(llm_provider="unsupported-provider")

    with pytest.raises(LLMError, match="ollama"):
        LLMFactory.create(settings=settings)