import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.workflow import Workflow
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowDefinition,
    WorkflowUpdate,
    attach_stacked_conditions,
    collect_agent_ids,
)


class UnknownAgentReferenceError(Exception):
    """Raised when a workflow references agent_id(s) that do not exist."""

    def __init__(self, missing: set[uuid.UUID]):
        self.missing = missing
        super().__init__(f"Unknown agent_id reference(s): {sorted(map(str, missing))}")


async def _assert_agents_exist(
    db: AsyncSession, definition: WorkflowDefinition
) -> None:
    ids = collect_agent_ids(definition)
    if not ids:
        return
    result = await db.execute(select(Agent.agent_id).where(Agent.agent_id.in_(ids)))
    existing = set(result.scalars().all())
    missing = ids - existing
    if missing:
        raise UnknownAgentReferenceError(missing)


async def create_workflow(db: AsyncSession, data: WorkflowCreate) -> Workflow:
    await _assert_agents_exist(db, data.definition)
    workflow = Workflow(
        name=data.name,
        # Enrich each agent node with its derived stacked_conditions at save time.
        definition=attach_stacked_conditions(data.definition.model_dump(mode="json")),
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    return workflow


async def get_workflow(db: AsyncSession, workflow_id: uuid.UUID) -> Workflow | None:
    return await db.get(Workflow, workflow_id)


async def list_workflows(
    db: AsyncSession, *, skip: int = 0, limit: int = 100
) -> list[Workflow]:
    result = await db.execute(
        select(Workflow).order_by(Workflow.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def update_workflow(
    db: AsyncSession, workflow: Workflow, payload: WorkflowUpdate
) -> Workflow:
    """Apply a partial update. A provided ``definition`` fully replaces the old
    one (after re-validating agent references); ``name`` is set if provided."""
    if payload.definition is not None:
        await _assert_agents_exist(db, payload.definition)
        # Reassign a fresh dict so SQLAlchemy detects the change; re-derive the
        # stacked conditions for the edited graph.
        workflow.definition = attach_stacked_conditions(
            payload.definition.model_dump(mode="json")
        )
    if payload.name is not None:
        workflow.name = payload.name

    await db.commit()
    await db.refresh(workflow)
    return workflow


async def delete_workflow(db: AsyncSession, workflow: Workflow) -> None:
    await db.delete(workflow)
    await db.commit()
