"""Unit tests for :class:`app.llm.client.OllamaClient`.

All tests use ``httpx.MockTransport`` (or a stub transport that raises
transport-level exceptions) to fully simulate the Ollama server. No
test in this module requires a running Ollama instance or performs
real network I/O.
"""

from collections.abc import Callable

import httpx
import pytest

from app.core.config import Settings
from app.llm.client import OllamaClient
from app.llm.exceptions import (
    LLMError,
    ModelNotFoundError,
    OllamaConnectionError,
    OllamaTimeoutError,
)
from app.llm.models import GenerationResult, HealthStatus, ModelList

TEST_HOST = "http://testserver"


def make_settings(**overrides: object) -> Settings:
    """Build a :class:`Settings` instance for testing, with overrides.

    Args:
        **overrides: Field values to override on top of test defaults.

    Returns:
        Settings: A settings instance suitable for constructing an
        :class:`OllamaClient` in isolation from the real environment.
    """
    defaults: dict[str, object] = {
        "ollama_host": TEST_HOST,
        "default_model": "llama3",
        "request_timeout": 5.0,
    }
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


def build_client(handler: Callable[[httpx.Request], httpx.Response]) -> OllamaClient:
    """Construct an :class:`OllamaClient` backed by a mock HTTP transport.

    Args:
        handler: A function that receives an ``httpx.Request`` and
            returns the ``httpx.Response`` the fake server should
            reply with.

    Returns:
        OllamaClient: A client whose HTTP calls are fully intercepted
        by ``handler`` — no real network access occurs.
    """
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(base_url=TEST_HOST, transport=transport)
    return OllamaClient(settings=make_settings(), http_client=http_client)


class TestHealthCheck:
    """Tests for :meth:`OllamaClient.health_check`."""

    def test_returns_available_on_success(self) -> None:
        """A 200 response should report the server as available."""

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            return httpx.Response(200, text="Ollama is running")

        client = build_client(handler)

        result = client.health_check()

        assert isinstance(result, HealthStatus)
        assert result.is_available is True

    def test_returns_unavailable_on_connect_error(self) -> None:
        """A connection failure should be reported, not raised."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        client = build_client(handler)

        result = client.health_check()

        assert result.is_available is False
        assert "unreachable" in result.message.lower()

    def test_returns_unavailable_on_timeout(self) -> None:
        """A timeout should be reported, not raised."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timed out", request=request)

        client = build_client(handler)

        result = client.health_check()

        assert result.is_available is False
        assert "timed out" in result.message.lower()

    def test_returns_unavailable_on_server_error(self) -> None:
        """A 5xx response should be reported as unavailable."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="internal error")

        client = build_client(handler)

        result = client.health_check()

        assert result.is_available is False


class TestListModels:
    """Tests for :meth:`OllamaClient.list_models`."""

    def test_returns_parsed_model_list(self) -> None:
        """A successful response should be parsed into ModelList."""

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/api/tags"
            return httpx.Response(
                200,
                json={
                    "models": [
                        {"name": "llama3", "size": 123, "digest": "abc"},
                        {"name": "mistral", "size": 456, "digest": "def"},
                    ]
                },
            )

        client = build_client(handler)

        result = client.list_models()

        assert isinstance(result, ModelList)
        assert len(result.models) == 2
        assert result.models[0].name == "llama3"
        assert result.models[1].size == 456

    def test_returns_empty_list_when_no_models(self) -> None:
        """An empty ``models`` field should yield an empty list, not an error."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"models": []})

        client = build_client(handler)

        result = client.list_models()

        assert result.models == []

    def test_raises_connection_error_when_unreachable(self) -> None:
        """A connection failure should raise OllamaConnectionError."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        client = build_client(handler)

        with pytest.raises(OllamaConnectionError):
            client.list_models()

    def test_raises_timeout_error_on_timeout(self) -> None:
        """A timeout should raise OllamaTimeoutError."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timed out", request=request)

        client = build_client(handler)

        with pytest.raises(OllamaTimeoutError):
            client.list_models()

    def test_raises_llm_error_on_server_error(self) -> None:
        """An unexpected 5xx response should raise the generic LLMError."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="internal error")

        client = build_client(handler)

        with pytest.raises(LLMError):
            client.list_models()

    def test_raises_llm_error_on_invalid_json(self) -> None:
        """A non-JSON response body should raise LLMError."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="not json")

        client = build_client(handler)

        with pytest.raises(LLMError):
            client.list_models()


class TestGenerate:
    """Tests for :meth:`OllamaClient.generate`."""

    def test_returns_generation_result_on_success(self) -> None:
        """A successful response should be parsed into GenerationResult."""

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.url.path == "/api/generate"
            return httpx.Response(
                200,
                json={"model": "llama3", "response": "Hello!", "done": True},
            )

        client = build_client(handler)

        result = client.generate(prompt="Say hello")

        assert isinstance(result, GenerationResult)
        assert result.response == "Hello!"
        assert result.model == "llama3"
        assert result.done is True

    def test_uses_default_model_when_none_provided(self) -> None:
        """Omitting the model argument should fall back to the default model."""
        captured_body: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal captured_body
            import json as json_module

            captured_body = json_module.loads(request.content)
            return httpx.Response(
                200, json={"model": "llama3", "response": "ok", "done": True}
            )

        client = build_client(handler)
        client.generate(prompt="Hi")

        assert captured_body["model"] == "llama3"

    def test_uses_explicit_model_when_provided(self) -> None:
        """An explicit model argument should override the default model."""
        captured_body: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal captured_body
            import json as json_module

            captured_body = json_module.loads(request.content)
            return httpx.Response(
                200, json={"model": "mistral", "response": "ok", "done": True}
            )

        client = build_client(handler)
        client.generate(prompt="Hi", model="mistral")

        assert captured_body["model"] == "mistral"

    def test_raises_model_not_found_on_404(self) -> None:
        """A 404 response should raise ModelNotFoundError."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, text="model not found")

        client = build_client(handler)

        with pytest.raises(ModelNotFoundError):
            client.generate(prompt="Hi", model="nonexistent-model")

    def test_raises_connection_error_when_unreachable(self) -> None:
        """A connection failure should raise OllamaConnectionError."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        client = build_client(handler)

        with pytest.raises(OllamaConnectionError):
            client.generate(prompt="Hi")

    def test_raises_timeout_error_on_timeout(self) -> None:
        """A timeout should raise OllamaTimeoutError."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timed out", request=request)

        client = build_client(handler)

        with pytest.raises(OllamaTimeoutError):
            client.generate(prompt="Hi")

    def test_raises_llm_error_on_unexpected_status(self) -> None:
        """A non-404 error status should raise the generic LLMError."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="internal error")

        client = build_client(handler)

        with pytest.raises(LLMError):
            client.generate(prompt="Hi")


class TestClientLifecycle:
    """Tests for construction, context-manager use, and shutdown."""

    def test_reads_configuration_from_settings(self) -> None:
        """The client should source host/model/timeout from Settings."""
        settings = make_settings(
            ollama_host="http://custom-host:1234",
            default_model="custom-model",
            request_timeout=9.0,
        )

        client = OllamaClient(settings=settings)

        assert client.host == "http://custom-host:1234"
        assert client.default_model == "custom-model"
        client.close()

    def test_context_manager_closes_underlying_client(self) -> None:
        """Using the client as a context manager should close it on exit."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="Ollama is running")

        with build_client(handler) as client:
            assert client.health_check().is_available is True
