from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_session
from app.models.defect_summary import DefectSummary

router = APIRouter(prefix="/summary", tags=["Defect Summary"])


class DefectSummaryOut(BaseModel):
    id: int
    lot_id: str
    defect_type: str
    count: int


@router.get("/list", response_model=list[DefectSummaryOut])
async def list_summary(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(DefectSummary))
    rows = result.scalars().all()
    return rows
