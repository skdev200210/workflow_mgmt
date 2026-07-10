from fastapi import APIRouter

from app.agent_types import build_catalog
from app.schemas.agent_types import AgentCatalog

router = APIRouter(tags=["agent-types"])


@router.get("/agent-types", response_model=AgentCatalog)
async def get_agent_types():
    """Catalog of agent categories and their child types + field schemas."""
    return build_catalog()
