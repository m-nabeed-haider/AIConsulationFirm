"""Ollama REST API client.

This module implements :class:`OllamaClient`, the single point of
communication between the application and a local Ollama server. No
other module should issue HTTP requests to Ollama directly — all
access must go through this client so that transport concerns (HTTP
status codes, timeouts, connection failures, response parsing) stay
isolated from the rest of the application.
"""

import httpx

from app.core.config import Settings, get_settings
from app.core.logger import logger
from app.llm.exceptions import (LLMError, ModelNotFoundError,
                                OllamaConnectionError, OllamaTimeoutError)
from app.llm.models import GenerationResult, HealthStatus, ModelInfo, ModelList

_HEALTH_CHECK_PATH: str = "/"
_LIST_MODELS_PATH: str = "/api/tags"
_GENERATE_PATH: str = "/api/generate"


class OllamaClient:
    """Synchronous client for communicating with a local Ollama server.

    This class is the single communication layer between the
    application and the Ollama REST API. It is responsible for
    building requests, performing HTTP calls, and translating both
    transport-level failures and API-level errors into the
    :mod:`app.llm.exceptions` hierarchy. Callers never see raw
    ``httpx`` exceptions or response objects.

    Attributes:
        host: Base URL of the Ollama server this client talks to.
        default_model: Model name used when :meth:`generate` is
            called without an explicit ``model`` argument.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Initialize the client.

        Args:
            settings: Application settings to source configuration
                from. Defaults to the shared, cached settings instance
                returned by :func:`app.core.config.get_settings`.
            http_client: An existing ``httpx.Client`` to use for
                requests. Primarily intended for dependency injection
                in tests; when omitted, a new client is created using
                the configured host and timeout.
        """
        resolved_settings = settings or get_settings()

        self.host: str = resolved_settings.ollama_host.rstrip("/")
        self.default_model: str = resolved_settings.default_model
        self._timeout: float = resolved_settings.request_timeout

        self._http_client: httpx.Client = http_client or httpx.Client(
            base_url=self.host,
            timeout=self._timeout,
        )

    def health_check(self) -> HealthStatus:
        """Check whether the Ollama server is reachable and responding.

        Unlike :meth:`list_models` and :meth:`generate`, this method
        does not raise on connectivity failure. It is designed to be
        safely polled (e.g. at application startup) to determine
        service availability.

        Returns:
            HealthStatus: The outcome of the connectivity check.
        """
        try:
            response = self._http_client.get(_HEALTH_CHECK_PATH)
            response.raise_for_status()
        except httpx.TimeoutException:
            logger.warning("Ollama health check timed out.")
            return HealthStatus(is_available=False, message="Health check timed out.")
        except httpx.HTTPError as exc:
            logger.warning("Ollama health check failed: {}", exc)
            return HealthStatus(
                is_available=False,
                message=f"Ollama server is unreachable: {exc}",
            )

        logger.debug("Ollama health check succeeded.")
        return HealthStatus(is_available=True, message="Ollama server is available.")

    def list_models(self) -> ModelList:
        """Retrieve the list of models available on the Ollama server.

        Returns:
            ModelList: The models currently available locally.

        Raises:
            OllamaConnectionError: If the server cannot be reached.
            OllamaTimeoutError: If the request exceeds the configured
                timeout.
            LLMError: If the server returns an unexpected error.
        """
        payload = self._request("GET", _LIST_MODELS_PATH)

        raw_models = payload.get("models", [])
        models = [
            ModelInfo(
                name=entry.get("name", ""),
                size=entry.get("size"),
                digest=entry.get("digest"),
            )
            for entry in raw_models
        ]

        logger.debug("Retrieved {} model(s) from Ollama.", len(models))
        return ModelList(models=models)

    def generate(self, prompt: str, model: str | None = None) -> GenerationResult:
        """Generate a text completion from the given prompt.

        Args:
            prompt: The input prompt to send to the model.
            model: Name of the model to use. Defaults to
                :attr:`default_model` when not provided.

        Returns:
            GenerationResult: The generated text and associated
            metadata.

        Raises:
            ModelNotFoundError: If the requested model does not exist
                on the Ollama server.
            OllamaConnectionError: If the server cannot be reached.
            OllamaTimeoutError: If the request exceeds the configured
                timeout.
            LLMError: If the server returns an unexpected error.
        """
        resolved_model = model or self.default_model
        request_body = {
            "model": resolved_model,
            "prompt": prompt,
            "stream": False,
        }

        payload = self._request(
            "POST",
            _GENERATE_PATH,
            json=request_body,
            model_for_error_context=resolved_model,
        )

        logger.debug("Generated response using model '{}'.", resolved_model)
        return GenerationResult(
            model=resolved_model,
            response=payload.get("response", ""),
            done=payload.get("done", True),
        )

    def close(self) -> None:
        """Release the underlying HTTP connection pool.

        Should be called when the client is no longer needed,
        typically at application shutdown. The client can also be
        used as a context manager, which calls this automatically.
        """
        self._http_client.close()

    def __enter__(self) -> "OllamaClient":
        """Enter the runtime context, returning this client instance."""
        return self

    def __exit__(self, *_exc_info: object) -> None:
        """Exit the runtime context, closing the underlying HTTP client."""
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        model_for_error_context: str | None = None,
    ) -> dict:
        """Perform an HTTP request and translate failures into LLM exceptions.

        Args:
            method: HTTP method to use (e.g. ``"GET"``, ``"POST"``).
            path: Request path, relative to :attr:`host`.
            json: Optional JSON request body.
            model_for_error_context: Model name to reference if the
                response indicates the model was not found. Only
                relevant for requests that operate on a specific
                model.

        Returns:
            dict: The parsed JSON response body.

        Raises:
            ModelNotFoundError: If the server responds with a 404 and
                a model name was supplied for context.
            OllamaConnectionError: If the server cannot be reached.
            OllamaTimeoutError: If the request exceeds the configured
                timeout.
            LLMError: If the server returns any other error, or the
                response body cannot be parsed as JSON.
        """
        try:
            response = self._http_client.request(method, path, json=json)
        except httpx.TimeoutException as exc:
            logger.error("Request to Ollama timed out: {} {}", method, path)
            raise OllamaTimeoutError(
                f"Request to Ollama server at '{self.host}' timed out "
                f"after {self._timeout} seconds."
            ) from exc
        except httpx.ConnectError as exc:
            logger.error("Failed to connect to Ollama server at '{}'.", self.host)
            raise OllamaConnectionError(
                f"Could not connect to Ollama server at '{self.host}'."
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("Unexpected transport error contacting Ollama: {}", exc)
            raise OllamaConnectionError(
                f"Unexpected network error contacting Ollama server "
                f"at '{self.host}': {exc}"
            ) from exc

        if response.status_code == httpx.codes.NOT_FOUND and model_for_error_context:
            logger.error(
                "Model '{}' not found on Ollama server.", model_for_error_context
            )
            raise ModelNotFoundError(
                f"Model '{model_for_error_context}' was not found on the "
                f"Ollama server at '{self.host}'."
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Ollama server returned an error status: {}", response.status_code
            )
            raise LLMError(
                f"Ollama server returned an unexpected status "
                f"{response.status_code}: {response.text}"
            ) from exc

        try:
            return response.json()
        except ValueError as exc:
            logger.error("Failed to parse Ollama response as JSON.")
            raise LLMError("Ollama server returned a non-JSON response.") from exc
