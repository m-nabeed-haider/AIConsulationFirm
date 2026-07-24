"""Unit tests for :class:`app.agents.registry.AgentRegistry`.

Agents are constructed with fully mocked ``BaseLLM``/``PromptManager``
dependencies, so nothing in this module requires a running Ollama
instance or any external service.
"""

from unittest.mock import MagicMock

import pytest

from app.agents.base import BaseAgent
from app.agents.exceptions import AgentError
from app.agents.registry import AgentRegistry
from app.llm.base import BaseLLM
from app.prompting.manager import PromptManager
from app.schemas.agent import AgentInfo
from app.schemas.enums import AgentRole


def make_agent(name: str, role: AgentRole = AgentRole.RESEARCH_ANALYST) -> BaseAgent:
    """Construct a BaseAgent with mocked dependencies for registry testing.

    Args:
        name: Name to give the agent's metadata.
        role: Role to give the agent's metadata.

    Returns:
        BaseAgent: A fully constructed agent, not yet registered.
    """
    return BaseAgent(
        metadata=AgentInfo(name=name, role=role),
        llm=MagicMock(spec=BaseLLM),
        prompt_manager=MagicMock(spec=PromptManager),
        prompt_template="system/research",
    )


class TestRegister:
    """Tests for AgentRegistry.register()."""

    def test_register_makes_agent_retrievable(self) -> None:
        """A registered agent should be retrievable via get()."""
        registry = AgentRegistry()
        agent = make_agent("Ava")

        registry.register(agent)

        assert registry.get("Ava") is agent

    def test_register_duplicate_name_raises_agent_error(self) -> None:
        """Registering two agents under the same name should raise AgentError."""
        registry = AgentRegistry()
        registry.register(make_agent("Ava"))

        with pytest.raises(AgentError):
            registry.register(make_agent("Ava"))

    def test_register_multiple_distinct_agents(self) -> None:
        """Multiple agents with distinct names should all register successfully."""
        registry = AgentRegistry()
        registry.register(make_agent("Ava", role=AgentRole.RESEARCH_ANALYST))
        registry.register(make_agent("Bo", role=AgentRole.REVIEWER))

        assert registry.get("Ava").metadata.role == AgentRole.RESEARCH_ANALYST
        assert registry.get("Bo").metadata.role == AgentRole.REVIEWER


class TestUnregister:
    """Tests for AgentRegistry.unregister()."""

    def test_unregister_removes_agent(self) -> None:
        """After unregistering, the agent should no longer be retrievable."""
        registry = AgentRegistry()
        registry.register(make_agent("Ava"))

        registry.unregister("Ava")

        with pytest.raises(AgentError):
            registry.get("Ava")

    def test_unregister_unknown_agent_raises_agent_error(self) -> None:
        """Unregistering a name that was never registered should raise AgentError."""
        registry = AgentRegistry()

        with pytest.raises(AgentError):
            registry.unregister("does-not-exist")

    def test_unregister_then_reregister_succeeds(self) -> None:
        """An unregistered name should be free to register again."""
        registry = AgentRegistry()
        first_agent = make_agent("Ava")
        registry.register(first_agent)
        registry.unregister("Ava")

        second_agent = make_agent("Ava")
        registry.register(second_agent)

        assert registry.get("Ava") is second_agent


class TestGet:
    """Tests for AgentRegistry.get()."""

    def test_get_unknown_agent_raises_agent_error(self) -> None:
        """Retrieving an unregistered name should raise AgentError, not KeyError."""
        registry = AgentRegistry()

        with pytest.raises(AgentError):
            registry.get("does-not-exist")

    def test_get_returns_exact_registered_instance(self) -> None:
        """get() should return the same object instance that was registered."""
        registry = AgentRegistry()
        agent = make_agent("Ava")
        registry.register(agent)

        assert registry.get("Ava") is agent


class TestListAgents:
    """Tests for AgentRegistry.list_agents()."""

    def test_list_agents_empty_registry(self) -> None:
        """An empty registry should list no agents."""
        registry = AgentRegistry()

        assert registry.list_agents() == []

    def test_list_agents_returns_metadata_for_each_registered_agent(self) -> None:
        """list_agents() should return AgentInfo metadata, not agent instances."""
        registry = AgentRegistry()
        registry.register(make_agent("Ava", role=AgentRole.RESEARCH_ANALYST))
        registry.register(make_agent("Bo", role=AgentRole.REVIEWER))

        listed = registry.list_agents()

        assert all(isinstance(item, AgentInfo) for item in listed)
        assert {info.name for info in listed} == {"Ava", "Bo"}

    def test_list_agents_reflects_unregistration(self) -> None:
        """Unregistering an agent should remove it from list_agents()."""
        registry = AgentRegistry()
        registry.register(make_agent("Ava"))
        registry.register(make_agent("Bo"))

        registry.unregister("Ava")

        names = {info.name for info in registry.list_agents()}
        assert names == {"Bo"}
