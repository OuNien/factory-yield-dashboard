from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.database import get_session
from app.models.lot import Lot

router = APIRouter()

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


# Delete
@router.delete("/delete/{lot_id}")
async def delete_lot(lot_id: str, session: AsyncSession = Depends(get_session)):
    row = await session.get(Lot, lot_id)
    if not row:
        raise HTTPException(404, f"{lot_id} not found")
    await session.delete(row)
    await session.commit()
    return {"status": "deleted", "lot_id": lot_id}
