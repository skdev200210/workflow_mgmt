import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExecutionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: uuid.UUID
    client_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    # One input CSV row: the initial variables the workflow needs
    # (e.g. name, phone_number, dpd, amount).
    input_row: dict[str, Any] = Field(default_factory=dict)


class ExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    seq_id: int
    workflow_execution_id: uuid.UUID
    workflow_id: uuid.UUID
    client_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    status: str
    executable_node_id: str | None = None
    input_file_row_json: dict[str, Any]
    context: dict[str, Any]
    callback_payloads: dict[str, Any]
    last_triggered_at: datetime | None = None
    next_trigger_at: datetime | None = None
    attempts: int
    max_attempts: int
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class AgentExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    seq_id: int
    agent_execution_id: uuid.UUID
    workflow_execution_id: uuid.UUID
    agent_id: uuid.UUID
    node_id: str
    attempt: int
    input_payload: dict[str, Any] | None = None
    output_payload: dict[str, Any] | None = None
    status: str
    created_at: datetime
    updated_at: datetime
