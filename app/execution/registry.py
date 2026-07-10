from typing import Any, Protocol

from app.agent_types import metadata_model_for_type
from app.execution.ai_calling import AiCallingExecutor, BlasterCallingExecutor
from app.execution.base import AgentExecutor
from app.execution.message import (
    MessageExecutor,
    RcsExecutor,
    SmsExecutor,
    WhatsAppExecutor,
)

_EXECUTORS: list[type[AgentExecutor]] = [
    AiCallingExecutor,
    BlasterCallingExecutor,
    MessageExecutor,  # legacy generic "message"
    SmsExecutor,
    RcsExecutor,
    WhatsAppExecutor,
]
EXECUTOR_BY_TYPE: dict[str, type[AgentExecutor]] = {e.agent_type: e for e in _EXECUTORS}


class _AgentLike(Protocol):
    agent_id: Any
    agent_type: str
    agent_metadata: dict[str, Any]


def build_executor(agent: _AgentLike) -> AgentExecutor:
    """Build the executor for an agent row (or any object exposing the same
    ``agent_id`` / ``agent_type`` / ``agent_metadata`` attributes).

    ``agent_metadata`` is re-validated through the type's category metadata model
    (single source of truth), then handed to the concrete executor. No DB
    session is required — usable standalone.
    """
    executor_cls = EXECUTOR_BY_TYPE.get(agent.agent_type)
    if executor_cls is None:
        raise ValueError(f"no executor for agent_type={agent.agent_type!r}")

    metadata = metadata_model_for_type(agent.agent_type).model_validate(agent.agent_metadata)
    return executor_cls(agent.agent_id, metadata)
