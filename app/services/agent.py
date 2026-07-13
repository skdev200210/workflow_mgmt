import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent_types import metadata_model_for_type, update_model_for_type
from app.models.agent import Agent
from app.schemas.agent import AgentUpdate


async def create_agent(db: AsyncSession, data: Any) -> Agent:
    """Create an agent from a validated AgentCreate (agent_metadata is a dict)."""
    agent = Agent(
        name=data.name,
        agent_type=data.agent_type,
        agent_metadata=data.agent_metadata,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


async def get_agent(db: AsyncSession, agent_id: uuid.UUID) -> Agent | None:
    return await db.get(Agent, agent_id)


async def list_agents(
    db: AsyncSession, *, skip: int = 0, limit: int = 100
) -> list[Agent]:
    result = await db.execute(
        select(Agent).order_by(Agent.created_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def update_agent(db: AsyncSession, agent: Agent, payload: AgentUpdate) -> Agent:
    """Rename and/or partially update agent_metadata, re-validating the result.

    A provided ``agent_metadata`` is validated against the type's partial update
    schema (rejecting unknown fields), merged onto the current metadata, and the
    merged result run back through the full validator so the input-variable
    f-string invariant still holds.
    """
    if payload.name is not None:
        agent.name = payload.name

    if payload.agent_metadata is not None:
        update_model = update_model_for_type(agent.agent_type)
        metadata_model = metadata_model_for_type(agent.agent_type)
        updates = update_model.model_validate(payload.agent_metadata).model_dump(
            exclude_unset=True
        )
        merged = {**agent.agent_metadata, **updates}
        validated = metadata_model.model_validate(merged)
        # Reassign a fresh dict so SQLAlchemy detects the change.
        agent.agent_metadata = validated.model_dump()

    await db.commit()
    await db.refresh(agent)
    return agent


async def delete_agent(db: AsyncSession, agent: Agent) -> None:
    await db.delete(agent)
    await db.commit()
