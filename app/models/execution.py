import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Identity,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.core.enums import AgentExecutionStatus, ExecutionStatus


class WorkflowExecution(Base, TimestampMixin):
    """One row per workflow run — this table IS the work queue.

    A seeder inserts one row per input CSV row (``input_file_row_json``),
    pointed at the workflow's start node. The worker claims due ``pending``
    rows and dispatches ``executable_node_id`` (resolving through any chain of
    decision nodes inline — decision nodes are never persisted here). Provider
    callbacks advance the row in place to the next agent node or complete it.

    ``context`` is the effective run context: it starts as a copy of the input
    row and accumulates callback outputs; decision conditions evaluate against
    it. ``input_file_row_json`` stays pristine as the audit copy.
    ``callback_payloads`` stores every callback received for this run, keyed by
    agent_execution_id (a list per key, so duplicates are kept too).
    """

    __tablename__ = "workflow_execution"

    seq_id: Mapped[int] = mapped_column(
        BigInteger, Identity(), unique=True, nullable=False
    )
    workflow_execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # pending -> processing -> in_flight -> (pending again on advance/retry)
    # terminal: completed | failed | dead_letter
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ExecutionStatus.PENDING.value
    )
    # The node the worker should trigger next. Always the start node or an
    # execute_agent node — decisions are resolved inline, never stored.
    executable_node_id: Mapped[str | None] = mapped_column(String(128))

    input_file_row_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    callback_payloads: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_trigger_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    error: Mapped[str | None] = mapped_column(Text)


class AgentExecution(Base, TimestampMixin):
    """One row per agent fire — the durable per-call/message history.

    ``agent_execution_id`` is the callback correlation id: the provider echoes
    it back so the callback can find this receipt, and through
    ``workflow_execution_id`` the run to advance. ``node_id`` + ``attempt``
    let a late callback for an old fire be detected as stale.
    """

    __tablename__ = "agent_execution"

    seq_id: Mapped[int] = mapped_column(
        BigInteger, Identity(), unique=True, nullable=False
    )
    agent_execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    node_id: Mapped[str] = mapped_column(String(128), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # What was (or would be) sent to the provider: run context + rendered request.
    input_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # The provider's callback, verbatim.
    output_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # dispatched -> callback_received | failed | stale | timed_out
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AgentExecutionStatus.DISPATCHED.value
    )
