"""Seed the workflow_execution table from a CSV — nothing else.

One pending workflow_execution row is inserted per CSV row
(input_file_row_json = the row), pointed at the workflow's start node. All
dispatching/advancing is done by the worker (`uv run python -m app.worker`)
and the /callbacks endpoint — this script never touches a run after insert.

The workflow must already exist (created via the UI or POST /workflows).
Set WORKFLOW_ID below to pick one, or leave it None to use the most recently
created workflow. Make sure the CSV columns cover the input variables the
workflow's agents/decisions need (e.g. name, dpd, amount).

Run:  uv run python scripts/seed_queue.py
"""

import asyncio
import csv
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.db.session import AsyncSessionLocal, engine  # noqa: E402
from app.execution.engine import start_execution  # noqa: E402
from app.models.workflow import Workflow  # noqa: E402

# --------------------------------------------------------------------------- #
# CONFIG — edit these instead of passing CLI args
# --------------------------------------------------------------------------- #
CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "input_rows.csv"
WORKFLOW_ID = (
    "d8d1127e-970e-4417-b8bd-4e432bd52c23"  # UUID string; None = latest workflow
)
CLIENT_ID: str | None = None  # optional UUID string


async def _pick_workflow(db) -> Workflow | None:
    if WORKFLOW_ID:
        return await db.get(Workflow, uuid.UUID(WORKFLOW_ID))
    return (
        (await db.execute(select(Workflow).order_by(Workflow.created_at.desc())))
        .scalars()
        .first()
    )


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        workflow = await _pick_workflow(db)
        if workflow is None:
            print("no workflow found - create one first (UI or POST /workflows),")
            print("or set WORKFLOW_ID in this script's CONFIG block")
            return
        print(f"workflow: {workflow.workflow_id}  ({workflow.name})")

        count = 0
        with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                customer_id = uuid.uuid4()
                execution = await start_execution(
                    db,
                    workflow=workflow,
                    client_id=uuid.UUID(CLIENT_ID) if CLIENT_ID else None,
                    customer_id=customer_id,
                    input_row=dict(row),
                )
                count += 1
                print(f"seeded  : {execution.workflow_execution_id}  row={dict(row)}")

    print(f"\nseeded {count} pending run(s) into workflow_execution.")
    print("Dispatch them with the worker:   uv run python -m app.worker")
    print(
        "Correlation ids for callbacks:   GET /executions/{workflow_execution_id}/agent-executions"
    )


async def main() -> None:
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
