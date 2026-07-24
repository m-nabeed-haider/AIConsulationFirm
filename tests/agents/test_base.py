"""Unit tests for :class:`app.agents.base.BaseAgent`.

``BaseLLM`` and ``PromptManager`` are fully mocked in every test here,
so nothing in this module requires a running Ollama instance, real
prompt templates on disk, or any other external service.
"""

from unittest.mock import MagicMock

import pytest

from app.agents.base import BaseAgent
from app.agents.context import AgentContext
from app.agents.exceptions import AgentExecutionError, InvalidTaskError
from app.llm.base import BaseLLM
from app.llm.exceptions import LLMError
from app.llm.response import LLMResponse
from app.prompting.exceptions import PromptError
from app.prompting.manager import PromptManager
from app.schemas.agent import AgentInfo
from app.schemas.enums import AgentRole, MessageType, TaskStatus
from app.schemas.message import Message
from app.schemas.task import Task

TEMPLATE_NAME = "system/research"


def make_metadata(**overrides: object) -> AgentInfo:
    """Build an AgentInfo for testing, with overrides.

    Args:
        **overrides: Field values to override on top of test defaults.

    Returns:
        AgentInfo: Metadata for a test agent.
    """
    defaults: dict[str, object] = {"name": "Ava", "role": AgentRole.RESEARCH_ANALYST}
    defaults.update(overrides)
    return AgentInfo(**defaults)  # type: ignore[arg-type]


def make_mock_llm(response_text: str = "Generated response") -> MagicMock:
    """Create a mock BaseLLM returning a canned LLMResponse.

    Args:
        response_text: Text the mock's generate() call should return.

    Returns:
        MagicMock: A mock spec'd against BaseLLM.
    """
    mock_llm = MagicMock(spec=BaseLLM)
    mock_llm.generate.return_value = LLMResponse(
        text=response_text, model="llama3", duration=0.05
    )
    return mock_llm


def make_mock_prompt_manager(rendered_text: str = "Rendered prompt") -> MagicMock:
    """Create a mock PromptManager returning canned rendered text.

    Args:
        rendered_text: Text the mock's render() call should return.

    Returns:
        MagicMock: A mock spec'd against PromptManager.
    """
    mock_pm = MagicMock(spec=PromptManager)
    mock_pm.render.return_value = rendered_text
    return mock_pm


def make_agent(
    llm: MagicMock | None = None,
    prompt_manager: MagicMock | None = None,
    metadata: AgentInfo | None = None,
    prompt_template: str = TEMPLATE_NAME,
) -> BaseAgent:
    """Construct a BaseAgent wired up with mocked dependencies.

    Args:
        llm: Mock LLM to inject. Defaults to a fresh mock.
        prompt_manager: Mock prompt manager to inject. Defaults to a
            fresh mock.
        metadata: Agent metadata to use. Defaults to a standard test
            agent.
        prompt_template: Template name the agent should use.

    Returns:
        BaseAgent: A fully constructed agent for testing.
    """
    return BaseAgent(
        metadata=metadata or make_metadata(),
        llm=llm or make_mock_llm(),
        prompt_manager=prompt_manager or make_mock_prompt_manager(),
        prompt_template=prompt_template,
    )


class TestExecuteLifecycle:
    """Tests for the overall execute() lifecycle and its return value."""

    def test_execute_returns_a_message(self) -> None:
        """execute() should return a Message instance."""
        agent = make_agent()
        task = Task(title="Research topic X")

        result = agent.execute(task)

        assert isinstance(result, Message)

    def test_message_sender_is_agent_name(self) -> None:
        """The returned message's sender should be the agent's name."""
        agent = make_agent(metadata=make_metadata(name="Ada"))
        task = Task(title="Research topic X")

        message = agent.execute(task)

        assert message.sender == "Ada"

    def test_message_content_is_llm_response_text(self) -> None:
        """The returned message's content should be the LLM's generated text."""
        agent = make_agent(llm=make_mock_llm(response_text="The answer is 42."))
        task = Task(title="Research topic X")

        message = agent.execute(task)

        assert message.content == "The answer is 42."

    def test_message_type_is_response(self) -> None:
        """The returned message's type should be RESPONSE."""
        agent = make_agent()
        task = Task(title="Research topic X")

        message = agent.execute(task)

        assert message.message_type == MessageType.RESPONSE

    def test_message_receiver_defaults_to_caller(self) -> None:
        """Without an explicit receiver, the message should default to 'caller'."""
        agent = make_agent()
        task = Task(title="Research topic X")

        message = agent.execute(task)

        assert message.receiver == "caller"

    def test_message_receiver_can_be_overridden(self) -> None:
        """An explicit receiver argument should be used instead of the default."""
        agent = make_agent()
        task = Task(title="Research topic X")

        message = agent.execute(task, receiver="supervisor")

        assert message.receiver == "supervisor"

    def test_execute_generates_execution_context_when_not_supplied(self) -> None:
        """Calling execute() without a context should not raise, and should proceed."""
        agent = make_agent()
        task = Task(title="Research topic X")

        message = agent.execute(task)

        assert isinstance(message, Message)

    def test_execute_accepts_explicit_context(self) -> None:
        """An explicitly supplied AgentContext should be accepted and used."""
        agent = make_agent()
        task = Task(title="Research topic X")
        context = AgentContext(metadata={"source": "test"})

        message = agent.execute(task, context=context)

        assert isinstance(message, Message)


class TestPromptRendering:
    """Tests verifying execute() correctly drives prompt rendering."""

    def test_render_called_with_configured_template_name(self) -> None:
        """PromptManager.render() should be called with the agent's template name."""
        mock_pm = make_mock_prompt_manager()
        agent = make_agent(prompt_manager=mock_pm, prompt_template="system/planner")
        task = Task(title="Plan project X")

        agent.execute(task)

        called_template_name = mock_pm.render.call_args.args[0]
        assert called_template_name == "system/planner"

    def test_render_called_with_task_derived_context(self) -> None:
        """The default build_prompt_context() output should be passed to render()."""
        mock_pm = make_mock_prompt_manager()
        agent = make_agent(prompt_manager=mock_pm)
        task = Task(title="Research topic X", description="Some description")

        agent.execute(task)

        called_context = mock_pm.render.call_args.args[1]
        assert called_context == {
            "task_title": "Research topic X",
            "task_description": "Some description",
        }

    def test_rendered_prompt_is_passed_to_llm(self) -> None:
        """The exact text returned by render() should be forwarded to the LLM."""
        mock_pm = make_mock_prompt_manager(rendered_text="Specific rendered prompt")
        mock_llm = make_mock_llm()
        agent = make_agent(llm=mock_llm, prompt_manager=mock_pm)
        task = Task(title="Research topic X")

        agent.execute(task)

        mock_llm.generate.assert_called_once_with("Specific rendered prompt")

    def test_prompt_error_raises_agent_execution_error(self) -> None:
        """A PromptError from the prompt manager should become an AgentExecutionError."""
        mock_pm = make_mock_prompt_manager()
        mock_pm.render.side_effect = PromptError("template not found")
        agent = make_agent(prompt_manager=mock_pm)
        task = Task(title="Research topic X")

        with pytest.raises(AgentExecutionError):
            agent.execute(task)

    def test_prompt_error_does_not_call_llm(self) -> None:
        """If prompt rendering fails, the LLM should never be invoked."""
        mock_pm = make_mock_prompt_manager()
        mock_pm.render.side_effect = PromptError("template not found")
        mock_llm = make_mock_llm()
        agent = make_agent(llm=mock_llm, prompt_manager=mock_pm)
        task = Task(title="Research topic X")

        with pytest.raises(AgentExecutionError):
            agent.execute(task)

        mock_llm.generate.assert_not_called()


class TestLLMInvocation:
    """Tests verifying execute() correctly drives LLM generation."""

    def test_llm_generate_called_exactly_once(self) -> None:
        """generate() should be called exactly once per execute() call."""
        mock_llm = make_mock_llm()
        agent = make_agent(llm=mock_llm)
        task = Task(title="Research topic X")

        agent.execute(task)

        mock_llm.generate.assert_called_once()

    def test_llm_error_raises_agent_execution_error(self) -> None:
        """An LLMError from the LLM should become an AgentExecutionError."""
        mock_llm = make_mock_llm()
        mock_llm.generate.side_effect = LLMError("connection refused")
        agent = make_agent(llm=mock_llm)
        task = Task(title="Research topic X")

        with pytest.raises(AgentExecutionError):
            agent.execute(task)

    def test_llm_error_message_is_informative(self) -> None:
        """The wrapped AgentExecutionError should reference the agent by name."""
        mock_llm = make_mock_llm()
        mock_llm.generate.side_effect = LLMError("connection refused")
        agent = make_agent(metadata=make_metadata(name="Ava"), llm=mock_llm)
        task = Task(title="Research topic X")

        with pytest.raises(AgentExecutionError, match="Ava"):
            agent.execute(task)


class TestInvalidTaskHandling:
    """Tests for BaseAgent.validate_task() and execute()'s task validation."""

    def test_non_task_object_raises_invalid_task_error(self) -> None:
        """Passing something other than a Task should raise InvalidTaskError."""
        agent = make_agent()

        with pytest.raises(InvalidTaskError):
            agent.execute("not a task")  # type: ignore[arg-type]

    def test_none_raises_invalid_task_error(self) -> None:
        """Passing None instead of a Task should raise InvalidTaskError."""
        agent = make_agent()

        with pytest.raises(InvalidTaskError):
            agent.execute(None)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "status", [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    )
    def test_non_executable_status_raises_invalid_task_error(
        self, status: TaskStatus
    ) -> None:
        """A task with a terminal status should not be executable."""
        agent = make_agent()
        task = Task(title="Already finished", status=status)

        with pytest.raises(InvalidTaskError):
            agent.execute(task)

    @pytest.mark.parametrize("status", [TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
    def test_executable_status_does_not_raise(self, status: TaskStatus) -> None:
        """Tasks with PENDING or IN_PROGRESS status should be executable."""
        agent = make_agent()
        task = Task(title="Still active", status=status)

        message = agent.execute(task)

        assert isinstance(message, Message)

    def test_invalid_task_error_prevents_prompt_rendering(self) -> None:
        """Validation should happen before any prompt rendering is attempted."""
        mock_pm = make_mock_prompt_manager()
        agent = make_agent(prompt_manager=mock_pm)
        task = Task(title="Already finished", status=TaskStatus.COMPLETED)

        with pytest.raises(InvalidTaskError):
            agent.execute(task)

        mock_pm.render.assert_not_called()


class TestBuildPromptContextHook:
    """Tests for the overridable build_prompt_context() hook."""

    def test_default_hook_maps_title_and_description(self) -> None:
        """The default implementation should expose task_title and task_description."""
        agent = make_agent()
        task = Task(title="A title", description="A description")
        context = AgentContext()

        result = agent.build_prompt_context(task, context)

        assert result == {"task_title": "A title", "task_description": "A description"}

    def test_subclass_can_override_prompt_context(self) -> None:
        """A subclass overriding build_prompt_context() should have it honored."""

        class CustomAgent(BaseAgent):
            def build_prompt_context(self, task: Task, context: AgentContext) -> dict:
                return {"custom_field": task.title.upper()}

        mock_pm = make_mock_prompt_manager()
        agent = CustomAgent(
            metadata=make_metadata(),
            llm=make_mock_llm(),
            prompt_manager=mock_pm,
            prompt_template=TEMPLATE_NAME,
        )
        task = Task(title="lowercase title")

        agent.execute(task)

        called_context = mock_pm.render.call_args.args[1]
        assert called_context == {"custom_field": "LOWERCASE TITLE"}


class TestDependencyInjection:
    """Tests confirming BaseAgent never constructs its own dependencies."""

    def test_agent_stores_injected_llm_and_prompt_manager(self) -> None:
        """The exact injected instances should be used, not new ones."""
        mock_llm = make_mock_llm()
        mock_pm = make_mock_prompt_manager()
        agent = make_agent(llm=mock_llm, prompt_manager=mock_pm)

        assert agent._llm is mock_llm
        assert agent._prompt_manager is mock_pm

    def test_base_module_does_not_construct_concrete_llm_or_prompt_manager(self) -> None:
        """app.agents.base should not import OllamaClient, OllamaProvider, or LLMFactory."""
        import inspect

        import app.agents.base as base_module

        source = inspect.getsource(base_module)

        assert "OllamaClient" not in source
        assert "OllamaProvider" not in source
        assert "LLMFactory" not in source
        assert "PromptLoader" not in source
        assert "PromptRenderer" not in source
