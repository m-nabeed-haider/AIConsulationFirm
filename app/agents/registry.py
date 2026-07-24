"""In-memory registry of available agents.

:class:`AgentRegistry` tracks agent instances by name, so a future
Supervisor (out of scope for this module) can look up and dispatch
work to the right agent by name without knowing how each agent was
constructed. This module contains no dispatch or orchestration logic
of its own — only registration and lookup.
"""

from app.agents.base import BaseAgent
from app.agents.exceptions import AgentError
from app.core.logger import logger
from app.schemas.agent import AgentInfo


class AgentRegistry:
    """Tracks available agent instances, keyed by agent name.

    This registry holds live :class:`BaseAgent` instances in memory
    for the lifetime of the process. It performs no persistence, no
    discovery, and no agent construction — callers are responsible for
    constructing an agent (with its dependencies injected) before
    registering it.
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """Register an agent, making it available for lookup by name.

        Args:
            agent: The agent instance to register, keyed by
                ``agent.metadata.name``.

        Raises:
            AgentError: If an agent is already registered under the
                same name.
        """
        name = agent.metadata.name

        if name in self._agents:
            raise AgentError(f"An agent named '{name}' is already registered.")

        self._agents[name] = agent
        logger.info("Registered agent '{}' (role='{}').", name, agent.metadata.role.value)

    def unregister(self, name: str) -> None:
        """Remove a previously registered agent.

        Args:
            name: Name of the agent to remove.

        Raises:
            AgentError: If no agent is registered under ``name``.
        """
        if name not in self._agents:
            raise AgentError(f"No agent named '{name}' is registered.")

        del self._agents[name]
        logger.info("Unregistered agent '{}'.", name)

    def get(self, name: str) -> BaseAgent:
        """Retrieve a registered agent by name.

        Args:
            name: Name of the agent to retrieve.

        Returns:
            BaseAgent: The registered agent instance.

        Raises:
            AgentError: If no agent is registered under ``name``.
        """
        try:
            return self._agents[name]
        except KeyError as exc:
            raise AgentError(f"No agent named '{name}' is registered.") from exc

    def list_agents(self) -> list[AgentInfo]:
        """List the metadata of every currently registered agent.

        Returns:
            list[AgentInfo]: Metadata for each registered agent, in
            registration order.
        """
        return [agent.metadata for agent in self._agents.values()]
