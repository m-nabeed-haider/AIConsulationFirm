"""Factory for constructing the configured LLM provider.

:class:`LLMFactory` is the only place in the application that knows
the mapping between a provider name (from configuration) and a
concrete :class:`app.llm.base.BaseLLM` implementation. Callers ask the
factory for a provider and depend on the returned ``BaseLLM``
interface only — they never import or instantiate a concrete provider
class directly.
"""

from app.core.config import Settings, get_settings
from app.core.logger import logger
from app.llm.base import BaseLLM
from app.llm.exceptions import LLMError
from app.llm.providers.ollama import OllamaProvider


class LLMFactory:
    """Constructs the :class:`BaseLLM` provider configured via ``LLM_PROVIDER``.

    New providers are added by registering them in
    :attr:`_PROVIDERS`; no other code needs to change. This module
    currently registers only ``"ollama"``, but the same pattern
    extends to future providers (OpenAI, Anthropic, Gemini, vLLM)
    without any change to agent or application code.
    """

    _PROVIDERS: dict[str, type[BaseLLM]] = {
        "ollama": OllamaProvider,
    }

    @classmethod
    def create(cls, settings: Settings | None = None) -> BaseLLM:
        """Create the ``BaseLLM`` provider configured via ``LLM_PROVIDER``.

        Args:
            settings: Application settings to read the provider name
                from. Defaults to the shared, cached settings instance
                returned by :func:`app.core.config.get_settings`.

        Returns:
            BaseLLM: An instance of the configured provider.

        Raises:
            LLMError: If the configured provider name is not
                registered in :attr:`_PROVIDERS`.
        """
        resolved_settings = settings or get_settings()
        provider_name = resolved_settings.llm_provider.strip().lower()

        provider_class = cls._PROVIDERS.get(provider_name)
        if provider_class is None:
            supported = ", ".join(sorted(cls._PROVIDERS))
            logger.error("Unsupported LLM provider requested: '{}'.", provider_name)
            raise LLMError(
                f"Unsupported LLM provider: '{provider_name}'. "
                f"Supported providers are: {supported}."
            )

        logger.info("Creating LLM provider '{}'.", provider_name)
        return provider_class()
