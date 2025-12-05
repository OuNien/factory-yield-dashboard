from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database.database import get_session
from app.models.lot import Lot
from app.models.yield_record import YieldRecord

router = APIRouter(tags=["Lot"])

class LotUpdate(BaseModel):
    product: Optional[str] = None
    station: Optional[str] = None
    total: Optional[int] = None
    good: Optional[int] = None

# Create
@router.post("/add")
async def add_lot(
    lot_id: str,
    product: str,
    station: str,
    total: int,
    good: int,
    session: AsyncSession = Depends(get_session)
):
    exist = await session.get(Lot, lot_id)
    if exist:
        raise HTTPException(400, f"Lot {lot_id} already exists")

    lot = Lot(
        lot_id=lot_id,
        product=product,
        station=station,
        total=total,
        good=good
    )
    session.add(lot)
    await session.commit()
    return {"status": "ok"}


# Read All
@router.get("/list")
async def list_lot(session: AsyncSession = Depends(get_session)):
    query = select(Lot)
    rows = (await session.execute(query)).scalars().all()
    return rows

@router.put("/update/{lot_id}")
async def update_lot(
    lot_id: str,
    payload: LotUpdate,
    session: AsyncSession = Depends(get_session),
):
    # 1. 取得資料
    lot = await session.get(Lot, lot_id)
    if not lot:
        raise HTTPException(404, f"{lot_id} not found")

    # 2. 更新有傳入的欄位
    update_data = payload.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(lot, key, value)

    # 3. commit
    await session.commit()
    await session.refresh(lot)

    return {
        "status": "updated",
        "lot_id": lot_id,
        "data": update_data
    }


# Delete
@router.delete("/delete/{lot_id}")
async def delete_lot(lot_id: str, session: AsyncSession = Depends(get_session)):
    lot = await session.get(Lot, lot_id)
    if not lot:
        raise HTTPException(404, f"{lot_id} not found")

    # 查是否有 yield_record 使用這個 lot_id
    result = await session.execute(
        select(YieldRecord).where(YieldRecord.lot_id == lot_id)
    )
    is_used = result.scalars().first() is not None

    if is_used:
        raise HTTPException(
            400,
            f"Cannot delete {lot_id}: It is referenced by yield_record"
        )

    await session.delete(lot)
    await session.commit()

    return {"status": "deleted", "lot_id": lot_id}

