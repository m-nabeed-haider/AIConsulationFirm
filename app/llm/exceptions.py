"""Custom exceptions for the LLM integration layer.

All errors raised by :mod:`app.llm.client` are instances of
:class:`LLMError` (or one of its subclasses). Callers outside this
package should catch :class:`LLMError` rather than any lower-level
HTTP or networking exception — the client is responsible for
translating those into this hierarchy so that raw transport details
never leak past its boundary.
"""


class LLMError(Exception):
    """Base exception for all errors raised by the LLM integration layer.

    Every other exception in :mod:`app.llm` inherits from this class,
    allowing callers to catch a single exception type when they do
    not need to distinguish between failure modes.
    """


class OllamaConnectionError(LLMError):
    """Raised when the Ollama server cannot be reached.

    This typically indicates the server is not running, the
    configured host is incorrect, or a network-level failure occurred
    before any HTTP response was received.
    """


class OllamaTimeoutError(LLMError):
    """Raised when a request to the Ollama server exceeds the configured timeout.

    See Also:
        app.core.config.Settings.request_timeout
    """


class ModelNotFoundError(LLMError):
    """Raised when a requested model is not available on the Ollama server.

    This is raised, for example, when :meth:`app.llm.client.OllamaClient.generate`
    is called with a model name that does not exist locally.
    """
