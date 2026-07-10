import uuid
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar

from pydantic import BaseModel

from app.schemas.agent import extract_placeholders


@dataclass
class ExecutionResult:
    """The outcome of executing an agent.

    For now execution is *simulated*: ``actions`` describes what the executor
    would do and ``rendered`` holds the templates filled with the run context.
    ``status`` leaves room for "success"/"failed" once real providers are wired.
    """

    agent_id: uuid.UUID
    agent_type: str
    status: str = "simulated"
    actions: list[str] = field(default_factory=list)
    rendered: dict[str, str] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)


class AgentExecutor(ABC):
    """Base class for the executable behaviour of an agent.

    Concrete executors are built from an agent's validated metadata (the config
    stored in the DB) and implement ``execute`` against a run-time context.
    """

    # Set by concrete subclasses; used by the registry to route agent types.
    agent_type: ClassVar[str]

    def __init__(self, agent_id: uuid.UUID, metadata: BaseModel):
        self.agent_id = agent_id
        self.metadata = metadata

    def _check_inputs(self, context: Mapping[str, Any]) -> None:
        """Ensure every declared input variable is present in the context."""
        declared = getattr(self.metadata, "input_variables", [])
        missing = [name for name in declared if name not in context]
        if missing:
            raise KeyError(f"context missing input variables: {missing}")

    def _render(self, template: str, context: Mapping[str, Any]) -> str:
        """Fill an f-string-style template from the context.

        Reuses ``extract_placeholders`` so render-time resolution matches the
        save-time validation exactly, then formats via ``str.format_map``.
        """
        missing = extract_placeholders(template) - set(context.keys())
        if missing:
            raise KeyError(f"context missing placeholders: {sorted(missing)}")
        return template.format_map(dict(context))

    @abstractmethod
    def execute(self, context: Mapping[str, Any]) -> ExecutionResult:
        """Run the agent against ``context`` and return the result."""
        raise NotImplementedError


class CallingExecutor(AgentExecutor, ABC):
    """Abstract base for all *calling* agent types (voice/phone channels)."""

    @abstractmethod
    def execute(self, context: Mapping[str, Any]) -> ExecutionResult:
        raise NotImplementedError


class MessageExecutorBase(AgentExecutor, ABC):
    """Abstract base for all *message* agent types (text channels)."""

    @abstractmethod
    def execute(self, context: Mapping[str, Any]) -> ExecutionResult:
        raise NotImplementedError
