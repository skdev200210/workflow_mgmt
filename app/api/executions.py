import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_api_key
from app.db.session import get_db
from app.execution.engine import start_execution
from app.models.execution import AgentExecution, WorkflowExecution
from app.models.workflow import Workflow
from app.schemas.execution import AgentExecutionRead, ExecutionCreate, ExecutionRead

router = APIRouter(
    prefix="/executions",
    tags=["executions"],
    dependencies=[Depends(require_api_key)],
)


@router.post("", response_model=ExecutionRead, status_code=status.HTTP_201_CREATED)
async def create_execution(
    payload: ExecutionCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    workflow = await db.get(Workflow, payload.workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        )
    return await start_execution(
        db,
        workflow=workflow,
        client_id=payload.client_id,
        customer_id=payload.customer_id,
        input_row=payload.input_row,
    )


@router.get("/{execution_id}", response_model=ExecutionRead)
async def get_execution(
    execution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    execution = await db.get(WorkflowExecution, execution_id)
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found"
        )
    return execution


@router.get("/{execution_id}/agent-executions", response_model=list[AgentExecutionRead])
async def list_agent_executions(
    execution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    result = await db.execute(
        select(AgentExecution)
        .where(AgentExecution.workflow_execution_id == execution_id)
        .order_by(AgentExecution.seq_id)
    )
    return list(result.scalars().all())
