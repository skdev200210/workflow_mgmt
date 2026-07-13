"""Workflow execution engine: fire-and-forget dispatch + callback-driven advance.

Model (single-table queue):
- ``workflow_execution`` holds ONE row per journey (customer x workflow run)
  and doubles as the work queue. Rows are seeded pointed at the workflow's
  start node with the CSV row in ``input_file_row_json``.
- The worker claims due ``pending`` rows and dispatches ``executable_node_id``.
  Any chain of decision/leaf nodes is resolved INLINE against the run context
  in the same claim — a decision node is never persisted as the executable
  node. When an agent node is reached it is dispatched (fire-and-forget): an
  ``agent_execution`` receipt is created (its UUID = the callback correlation
  id) and the row goes ``in_flight``.
- The external service reports the outcome via POST /callbacks. The callback
  is stored verbatim in ``callback_payloads``, captured outputs merge into
  ``context``, and the row advances in place to the next agent node (again
  resolved through any stacked decisions), retries, or completes.

No caching: the workflow definition is read fresh from the workflows table on
every dispatch/callback.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.execution.base import ExecutionResult
from app.execution.conditions import MissingParamError, select_next_edge
from app.execution.registry import build_executor
from app.models.agent import Agent
from app.models.execution import AgentExecution, WorkflowExecution
from app.models.workflow import Workflow

logger = logging.getLogger(__name__)

# Safety cap on inline decision-chain traversal (guards decision-only cycles).
_MAX_DECISION_HOPS = 50


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def get_workflow_definition(
    db: AsyncSession, workflow_id: uuid.UUID
) -> dict[str, Any]:
    """Read the definition fresh from the workflows table (no caching)."""
    wf = await db.get(Workflow, workflow_id)
    if wf is None:
        raise ValueError(f"workflow {workflow_id} not found")
    return wf.definition


def _result_to_json(result: ExecutionResult) -> dict[str, Any]:
    return {
        "agent_id": str(result.agent_id),
        "agent_type": result.agent_type,
        "status": result.status,
        "actions": result.actions,
        "rendered": result.rendered,
        "outputs": result.outputs,
    }


def _is_end_leaf(node: dict[str, Any]) -> bool:
    return node.get("type") == "leaf_node" and not node.get("edges")


def resolve_next_actionable(
    definition: dict[str, Any], from_node: dict[str, Any], context: dict[str, Any]
) -> tuple[str, str | None, dict[str, Any] | None]:
    """Follow edges from ``from_node`` through stacked decision/leaf nodes to
    the next ACTIONABLE node.

    Decision nodes are evaluated inline against ``context`` (their True/False
    branch is followed immediately), so any number of stacked filters collapse
    into a single hop. Returns:
      ("agent", node_id, node_def)  -- next execute_agent node to dispatch
      ("end", node_id, node_def)    -- a terminal leaf was reached
      ("none", None, None)          -- no edge matched / hop cap hit (branch ends)
    """
    nodes = definition["nodes"]
    current = from_node
    for _ in range(_MAX_DECISION_HOPS):
        edge = select_next_edge(current, context)
        if edge is None:
            return ("none", None, None)
        target_id = edge["target"]
        target = nodes[target_id]
        if target.get("type") == "execute_agent":
            return ("agent", target_id, target)
        if _is_end_leaf(target):
            return ("end", target_id, target)
        # Intermediate leaf or another decision: keep walking.
        current = target
    logger.warning(
        "decision-chain hop cap (%s) reached; ending branch", _MAX_DECISION_HOPS
    )
    return ("none", None, None)


def _retry_delay_seconds(definition: dict[str, Any]) -> int:
    """Retry delay from calling_config.call_not_answered.retry, else default."""
    settings = get_settings()
    retry = (
        (definition.get("calling_config") or {})
        .get("call_not_answered", {})
        .get("retry", {})
    )
    value = retry.get("value")
    units = str(retry.get("units", "")).lower()
    if not isinstance(value, (int, float)) or value <= 0:
        return settings.default_retry_seconds
    if units.startswith("hr") or units.startswith("hour"):
        return int(value * 3600)
    if units.startswith("min"):
        return int(value * 60)
    if units.startswith("day"):
        return int(value * 86400)
    return settings.default_retry_seconds


def _finish(
    execution: WorkflowExecution, *, status: str, error: str | None = None
) -> None:
    """Move the run to a terminal status (completed | failed | dead_letter)."""
    execution.status = status
    execution.error = error
    execution.next_trigger_at = None
    logger.log(
        logging.INFO if status == "completed" else logging.WARNING,
        "run finished",
        extra={
            "event": f"run_{status}",
            "workflow_execution_id": execution.workflow_execution_id,
            "node_id": execution.executable_node_id,
            "error": error,
        },
    )


def _record_callback(
    execution: WorkflowExecution,
    agent_execution_id: uuid.UUID,
    payload_json: dict[str, Any],
) -> None:
    """Append the raw callback under its correlation id (list per key, so every
    callback — including duplicates — is kept). Reassigned so SQLAlchemy sees
    the JSONB change."""
    key = str(agent_execution_id)
    payloads = dict(execution.callback_payloads or {})
    payloads[key] = [*payloads.get(key, []), payload_json]
    execution.callback_payloads = payloads


# --------------------------------------------------------------------------- #
# Start — seed one row pointed at the workflow's start node
# --------------------------------------------------------------------------- #
async def start_execution(
    db: AsyncSession,
    *,
    workflow: Workflow,
    client_id: uuid.UUID | None,
    customer_id: uuid.UUID | None,
    input_row: dict[str, Any],
) -> WorkflowExecution:
    """Create one pending run pointed at the start node.

    No graph walking happens here — the worker resolves decisions inline when
    it claims the row. ``input_row`` (a CSV row / initial variables) becomes
    both the immutable ``input_file_row_json`` and the initial ``context``.
    """
    execution = WorkflowExecution(
        workflow_id=workflow.workflow_id,
        client_id=client_id,
        customer_id=customer_id,
        status="pending",
        executable_node_id=workflow.definition.get("workflow_start"),
        input_file_row_json=dict(input_row),
        context=dict(input_row),
        max_attempts=get_settings().default_max_attempts,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    return execution


# --------------------------------------------------------------------------- #
# Dispatch (worker side) — fire and forget
# --------------------------------------------------------------------------- #
async def dispatch_execution(
    db: AsyncSession, execution: WorkflowExecution
) -> uuid.UUID | None:
    """Dispatch one claimed run and forget.

    If ``executable_node_id`` is not an agent node (start node, or a decision
    pointed at by a callback), the decision chain is resolved inline against
    the run context first — the row never waits on a decision node. When an
    agent node is reached: build the request from the stored agent config,
    create an ``agent_execution`` receipt (its UUID = the callback correlation
    id), and mark the row ``in_flight``. NO advance happens here — the callback
    advances the row.

    Returns the agent_execution_id when a dispatch happened, else None.
    """
    try:
        definition = await get_workflow_definition(db, execution.workflow_id)
    except ValueError as exc:
        _finish(execution, status="failed", error=str(exc))
        await db.commit()
        return None

    node = definition["nodes"].get(execution.executable_node_id)
    if node is None:
        _finish(
            execution,
            status="failed",
            error=f"node {execution.executable_node_id!r} not found in workflow definition",
        )
        await db.commit()
        return None

    # Not an agent node: walk through decisions/leaves inline until we hit one.
    if node.get("type") != "execute_agent":
        source_node_id = execution.executable_node_id
        try:
            kind, node_id, node_def = resolve_next_actionable(
                definition, node, execution.context
            )
        except MissingParamError as exc:
            _finish(execution, status="failed", error=str(exc))
            await db.commit()
            return None
        if kind != "agent":
            _finish(execution, status="completed")
            execution.last_triggered_at = _now()
            await db.commit()
            return None
        execution.executable_node_id = node_id
        node = node_def
        logger.info(
            "decisions resolved inline",
            extra={
                "event": "decisions_resolved",
                "workflow_execution_id": execution.workflow_execution_id,
                "from_node": source_node_id,
                "to_node": node_id,
            },
        )

    agent_id = (node.get("node_config") or {}).get("agent_id")
    agent = await db.get(
        Agent, uuid.UUID(agent_id) if isinstance(agent_id, str) else agent_id
    )
    if agent is None:
        _finish(execution, status="failed", error=f"agent {agent_id} not found")
        await db.commit()
        return None

    now = _now()
    executor = build_executor(agent)
    # Simulated dispatch: execute() builds the rendered request payload. A real
    # provider integration would POST this to the service together with the
    # agent_execution_id (correlation id) and the /callbacks URL.
    result = executor.execute(execution.context)

    receipt = AgentExecution(
        workflow_execution_id=execution.workflow_execution_id,
        agent_id=agent.agent_id,
        node_id=execution.executable_node_id,
        attempt=execution.attempts,
        input_payload={
            "context": dict(execution.context),
            "request": _result_to_json(result),
        },
        status="dispatched",
    )
    db.add(receipt)
    await db.flush()  # assign agent_execution_id

    execution.status = "in_flight"
    execution.last_triggered_at = now
    execution.next_trigger_at = None
    execution.error = None
    await db.commit()
    logger.info(
        "agent dispatched",
        extra={
            "event": "agent_dispatched",
            "workflow_execution_id": execution.workflow_execution_id,
            "node_id": execution.executable_node_id,
            "agent_id": agent.agent_id,
            "agent_type": agent.agent_type,
            "agent_execution_id": receipt.agent_execution_id,
            "attempt": execution.attempts,
        },
    )
    return receipt.agent_execution_id


# --------------------------------------------------------------------------- #
# Callback (external service side) — record outcome and advance in place
# --------------------------------------------------------------------------- #
async def apply_callback(db: AsyncSession, payload: Any) -> dict[str, Any]:
    """Apply one provider callback. Idempotent and stale-safe:

    - unknown agent_execution_id       -> LookupError (404 at the API layer)
    - receipt already finalized        -> recorded, otherwise a no-op
    - run moved on / attempt mismatch  -> receipt marked stale, no-op

    Every callback (including duplicates and stale ones) is appended to the
    run's ``callback_payloads``.
    """
    receipt = await db.get(
        AgentExecution, payload.agent_execution_id, with_for_update=True
    )
    if receipt is None:
        raise LookupError(f"unknown agent_execution_id {payload.agent_execution_id}")

    execution = await db.get(
        WorkflowExecution, receipt.workflow_execution_id, with_for_update=True
    )
    now = _now()
    payload_json = payload.model_dump(mode="json")
    if execution is not None:
        _record_callback(execution, receipt.agent_execution_id, payload_json)

    log_ctx = {
        "workflow_execution_id": receipt.workflow_execution_id,
        "agent_execution_id": receipt.agent_execution_id,
        "node_id": receipt.node_id,
        "source": payload.source,
        "outcome": payload.outcome,
    }
    logger.info("callback received", extra={"event": "callback_received", **log_ctx})

    if receipt.status != "dispatched":
        await db.commit()
        logger.info(
            "duplicate callback ignored",
            extra={
                "event": "callback_duplicate",
                "receipt_status": receipt.status,
                **log_ctx,
            },
        )
        return {"processed": False, "reason": f"already finalized ({receipt.status})"}

    def _finish_receipt(status: str) -> None:
        receipt.status = status
        receipt.output_payload = payload_json

    # Stale: the run was swept/re-dispatched or already advanced past this fire.
    if (
        execution is None
        or execution.status != "in_flight"
        or execution.executable_node_id != receipt.node_id
        or execution.attempts != receipt.attempt
    ):
        _finish_receipt("stale")
        await db.commit()
        logger.warning(
            "stale callback (run has moved on)",
            extra={"event": "callback_stale", **log_ctx},
        )
        return {"processed": False, "reason": "stale callback (run has moved on)"}

    if payload.outcome == "failure":
        _finish_receipt("failed")
        _finish(
            execution,
            status="failed",
            error=payload.status or "callback reported failure",
        )
        await db.commit()
        return _run_state(execution, processed=True)

    try:
        definition = await get_workflow_definition(db, execution.workflow_id)
    except ValueError as exc:
        _finish_receipt("failed")
        _finish(execution, status="failed", error=str(exc))
        await db.commit()
        return _run_state(execution, processed=True)

    if payload.outcome == "retry":
        _finish_receipt("callback_received")
        if execution.attempts >= execution.max_attempts:
            _finish(
                execution,
                status="dead_letter",
                error=f"max attempts ({execution.max_attempts}) reached at node {execution.executable_node_id}",
            )
        else:
            execution.status = "pending"
            execution.next_trigger_at = payload.next_trigger_at or (
                now + timedelta(seconds=_retry_delay_seconds(definition))
            )
            logger.info(
                "retry scheduled",
                extra={
                    "event": "retry_scheduled",
                    "attempt": execution.attempts,
                    "max_attempts": execution.max_attempts,
                    "next_trigger_at": execution.next_trigger_at,
                    **log_ctx,
                },
            )
        await db.commit()
        return _run_state(execution, processed=True)

    # outcome == "success": merge outputs, then advance through stacked decisions.
    _finish_receipt("callback_received")
    merged = {**execution.context, **(payload.outputs or {})}
    execution.context = merged

    current_node = definition["nodes"][execution.executable_node_id]
    try:
        kind, node_id, _node_def = resolve_next_actionable(
            definition, current_node, merged
        )
    except MissingParamError as exc:
        _finish(execution, status="failed", error=str(exc))
        await db.commit()
        return _run_state(execution, processed=True)
    if kind == "agent":
        execution.executable_node_id = node_id
        execution.status = "pending"
        execution.attempts = 0  # each node gets a fresh attempt budget
        execution.next_trigger_at = payload.next_trigger_at
        execution.error = None
        logger.info(
            "run advanced",
            extra={
                "event": "run_advanced",
                "to_node": node_id,
                "merged_outputs": list((payload.outputs or {}).keys()),
                **log_ctx,
            },
        )
    else:
        _finish(execution, status="completed")

    await db.commit()
    return _run_state(execution, processed=True)


def _run_state(execution: WorkflowExecution, *, processed: bool) -> dict[str, Any]:
    return {
        "processed": processed,
        "reason": None,
        "workflow_execution_id": execution.workflow_execution_id,
        "status": execution.status,
        "executable_node_id": execution.executable_node_id,
        "next_trigger_at": execution.next_trigger_at,
    }
