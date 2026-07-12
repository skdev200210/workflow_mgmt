import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CallbackPayload(BaseModel):
    """One callback shape for ALL external services (calling + messaging).

    ``agent_execution_id`` is the correlation id we issue at dispatch time — the
    provider must echo it back; it uniquely identifies the run, the node, and
    the specific attempt (so duplicate/late callbacks are detected safely).
    """

    model_config = ConfigDict(extra="forbid")

    agent_execution_id: uuid.UUID
    source: Literal["calling", "whatsapp", "sms", "rcs"]
    # Normalized outcome that drives the engine:
    #   success -> merge outputs, advance to the next node (through decisions)
    #   retry   -> re-schedule the SAME node (e.g. call not answered), bounded
    #              by max_attempts, delay from next_trigger_at or calling_config
    #   failure -> row + run marked failed
    outcome: Literal["success", "retry", "failure"]
    # Provider-specific detail, e.g. "no_answer", "busy", "undelivered".
    status: str | None = None
    # Captured output variables (e.g. {"ptp": true}) — merged into the context
    # and available to downstream decision nodes.
    outputs: dict[str, Any] = Field(default_factory=dict)
    # Raw provider payload, stored verbatim on the agent_execution receipt.
    result: dict[str, Any] | None = None
    # When the NEXT step (or the retry) should run; omitted = immediately
    # (retry falls back to the workflow's calling_config interval).
    next_trigger_at: datetime | None = None


class CallbackResponse(BaseModel):
    processed: bool
    reason: str | None = None
    workflow_execution_id: uuid.UUID | None = None
    status: str | None = None
    executable_node_id: str | None = None
    next_trigger_at: datetime | None = None
