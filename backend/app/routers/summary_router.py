from aiobreaker import CircuitBreakerError
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.common.circuit_breakers import postgres_breaker, circuit_open_counter
from app.database.database import get_session
from app.models.defect_summary import DefectSummary

router = APIRouter(prefix="/summary", tags=["Defect Summary"])


class DefectSummaryOut(BaseModel):
    id: int
    lot_id: str
    defect_type: str
    count: int


@router.get("/list", response_model=list[DefectSummaryOut])
@postgres_breaker
async def list_summary(session: AsyncSession = Depends(get_session)):
    try:
        result = await session.execute(select(DefectSummary))
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )

    rows = result.scalars().all()
    return rows
