import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExecutionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: uuid.UUID
    client_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    phone_number: str | None = Field(None, max_length=20)
    # Initial variables the workflow needs (e.g. name, dpd, amount).
    context: dict[str, Any] = Field(default_factory=dict)


class ExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workflow_execution_id: uuid.UUID
    workflow_id: uuid.UUID
    client_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    phone_number: str | None = None
    status: str
    context: dict[str, Any]
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class AgentExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent_execution_id: uuid.UUID
    workflow_execution_id: uuid.UUID
    node_id: str
    agent_id: uuid.UUID
    agent_type: str
    attempt: int
    input_context: dict[str, Any] | None = None
    request_payload: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    output_variables: dict[str, Any] | None = None
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    created_at: datetime
