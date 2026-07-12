"""Queue worker: claims due workflow_execution rows and dispatches them
(fire-and-forget), plus a sweeper that reclaims in_flight rows whose callback
never arrived.

Run with:  python -m app.worker

``workflow_execution`` IS the queue — there is no separate queue table.
Claiming uses ``FOR UPDATE SKIP LOCKED`` so many workers can run concurrently
against the same table without stepping on each other. Rows advance via the
/callbacks endpoint, not here. All statements are built with the SQLAlchemy
ORM expression language (no raw SQL).
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select, update

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import AsyncSessionLocal
from app.execution.engine import dispatch_execution
from app.models.execution import AgentExecution, WorkflowExecution

setup_logging()
logger = logging.getLogger("worker")


def _claim_stmt(batch: int):
    """Atomically claim up to ``batch`` due rows (SKIP LOCKED under the hood)."""
    claimed = (
        select(WorkflowExecution.workflow_execution_id)
        .where(
            WorkflowExecution.status == "pending",
            or_(
                WorkflowExecution.next_trigger_at.is_(None),
                WorkflowExecution.next_trigger_at <= func.now(),
            ),
        )
        .order_by(WorkflowExecution.next_trigger_at)
        .limit(batch)
        .with_for_update(skip_locked=True)
        .cte("claimed")
    )
    return (
        update(WorkflowExecution)
        .where(WorkflowExecution.workflow_execution_id == claimed.c.workflow_execution_id)
        .values(status="processing", attempts=WorkflowExecution.attempts + 1)
        .returning(WorkflowExecution.workflow_execution_id)
    )


# Sweeper: in_flight rows whose callback never arrived. The deadline is derived
# (last_triggered_at + dispatch_timeout_seconds) — no timeout column. Attempts
# remaining -> back to pending (re-dispatched next poll); exhausted ->
# dead_letter. Their dispatched receipts are marked timed_out so a late
# callback is detected as stale/duplicate.
def _timeout_cutoff() -> datetime:
    return datetime.now(timezone.utc) - timedelta(
        seconds=get_settings().dispatch_timeout_seconds
    )


def _sweep_retry_stmt():
    return (
        update(WorkflowExecution)
        .where(
            WorkflowExecution.status == "in_flight",
            WorkflowExecution.last_triggered_at <= _timeout_cutoff(),
            WorkflowExecution.attempts < WorkflowExecution.max_attempts,
        )
        .values(
            status="pending",
            next_trigger_at=func.now(),
            error="callback timed out",
        )
        .returning(WorkflowExecution.workflow_execution_id)
    )


def _sweep_dead_stmt():
    return (
        update(WorkflowExecution)
        .where(
            WorkflowExecution.status == "in_flight",
            WorkflowExecution.last_triggered_at <= _timeout_cutoff(),
            WorkflowExecution.attempts >= WorkflowExecution.max_attempts,
        )
        .values(
            status="dead_letter",
            next_trigger_at=None,
            error="callback timed out; max attempts reached",
        )
        .returning(WorkflowExecution.workflow_execution_id)
    )


def _sweep_receipts_stmt(execution_ids: list[uuid.UUID]):
    return (
        update(AgentExecution)
        .where(
            AgentExecution.status == "dispatched",
            AgentExecution.workflow_execution_id.in_(execution_ids),
        )
        .values(status="timed_out")
    )


async def _claim(batch: int) -> list[uuid.UUID]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(_claim_stmt(batch))
        ids = [r[0] for r in result.all()]
        await db.commit()
    return ids


async def _dispatch_one(execution_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as db:
        execution = await db.get(WorkflowExecution, execution_id)
        if execution is None:
            return
        try:
            await dispatch_execution(db, execution)
        except Exception as exc:  # noqa: BLE001 — isolate per-row failures
            logger.exception(
                "dispatch failed",
                extra={"event": "dispatch_error", "workflow_execution_id": execution_id},
            )
            await db.rollback()
            async with AsyncSessionLocal() as db2:
                ex = await db2.get(WorkflowExecution, execution_id)
                if ex is not None:
                    ex.status = "failed"
                    ex.error = str(exc)
                    await db2.commit()


async def sweep_timeouts() -> int:
    """Reclaim in_flight rows whose callback deadline passed."""
    async with AsyncSessionLocal() as db:
        retried = [r[0] for r in (await db.execute(_sweep_retry_stmt())).all()]
        dead = [r[0] for r in (await db.execute(_sweep_dead_stmt())).all()]
        swept = retried + dead
        if swept:
            await db.execute(_sweep_receipts_stmt(swept))
            logger.warning(
                "sweeper reclaimed timed-out runs",
                extra={
                    "event": "sweep",
                    "retried": [str(i) for i in retried],
                    "dead_lettered": [str(i) for i in dead],
                },
            )
        await db.commit()
    return len(swept)


async def process_available(batch: int | None = None) -> int:
    """Sweep timeouts, then claim and dispatch one batch of due rows."""
    settings = get_settings()
    await sweep_timeouts()
    execution_ids = await _claim(batch or settings.worker_batch_size)
    for execution_id in execution_ids:
        await _dispatch_one(execution_id)
    return len(execution_ids)


async def run_worker() -> None:
    settings = get_settings()
    logger.info(
        "worker started",
        extra={
            "event": "worker_started",
            "batch_size": settings.worker_batch_size,
            "poll_interval": settings.worker_poll_interval,
            "dispatch_timeout_seconds": settings.dispatch_timeout_seconds,
        },
    )
    while True:
        processed = await process_available()
        if processed:
            logger.info(
                "batch dispatched", extra={"event": "batch_dispatched", "count": processed}
            )
        else:
            await asyncio.sleep(settings.worker_poll_interval)


if __name__ == "__main__":
    asyncio.run(run_worker())
