import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Identity,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class WorkflowExecution(Base, TimestampMixin):
    """One row per workflow run (a customer/phone going through one workflow)."""

    __tablename__ = "workflow_execution"

    seq_id: Mapped[int] = mapped_column(BigInteger, Identity(), unique=True, nullable=False)
    workflow_execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    phone_number: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    current_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    parent_workflow_execution_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)


class WorkflowQueue(Base, TimestampMixin):
    """The work/scheduling table. A worker claims due rows and processes them."""

    __tablename__ = "workflow_queue"

    row_id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    workflow_execution_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    customer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    phone_number: Mapped[str | None] = mapped_column(String(20))

    node_id: Mapped[str] = mapped_column(String(128), nullable=False)
    node_type: Mapped[str] = mapped_column(String(32), nullable=False)
    agent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    executable_node: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    node_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    source_node_id: Mapped[str | None] = mapped_column(String(128))
    source_edge_id: Mapped[str | None] = mapped_column(String(128))

    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_trigger_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    execution_timeout_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    parent_workflow_execution_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    error: Mapped[str | None] = mapped_column(Text)


class AgentExecution(Base, TimestampMixin):
    """One row per agent fire — the durable per-call/message history."""

    __tablename__ = "agent_execution"

    seq_id: Mapped[int] = mapped_column(BigInteger, Identity(), unique=True, nullable=False)
    agent_execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workflow_execution_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    workflow_queue_row_id: Mapped[int | None] = mapped_column(BigInteger)
    node_id: Mapped[str] = mapped_column(String(128), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    agent_type: Mapped[str] = mapped_column(String(32), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    input_context: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    request_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    output_variables: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="executed")

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
