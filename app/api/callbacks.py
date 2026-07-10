from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_api_key
from app.db.session import get_db
from app.execution.engine import apply_callback
from app.schemas.callback import CallbackPayload, CallbackResponse

# Single entry point for ALL provider callbacks (calling, whatsapp, sms, rcs).
router = APIRouter(
    prefix="/callbacks",
    tags=["callbacks"],
    dependencies=[Depends(require_api_key)],
)


@router.post("", response_model=CallbackResponse)
async def receive_callback(
    payload: CallbackPayload,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Record a provider outcome and advance the corresponding queue row.

    Idempotent: duplicate callbacks for an already-finalized dispatch, and late
    callbacks for a row that has moved on (retry/sweep), are acknowledged with
    ``processed: false`` instead of erroring.
    """
    try:
        return await apply_callback(db, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
