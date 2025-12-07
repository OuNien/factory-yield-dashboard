from aiobreaker import CircuitBreakerError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from starlette import status

from app.common.cache_key import clear_yield_trend_cache
from app.common.circuit_breakers import postgres_breaker, circuit_open_counter
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
@postgres_breaker
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
    try:
        await session.commit()
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )

    clear_yield_trend_cache()
    return {"status": "ok"}


# Read All
@router.get("/list")
@postgres_breaker
async def list_lot(session: AsyncSession = Depends(get_session)):
    query = select(Lot)
    try:
        rows = (await session.execute(query)).scalars().all()
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )

    return rows

@router.put("/update/{lot_id}")
@postgres_breaker
async def update_lot(
    lot_id: str,
    payload: LotUpdate,
    session: AsyncSession = Depends(get_session),
):
    # 1. 取得資料
    try:
        lot = await session.get(Lot, lot_id)
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )

    if not lot:
        raise HTTPException(404, f"{lot_id} not found")

    # 2. 更新有傳入的欄位
    update_data = payload.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(lot, key, value)

    # 3. commit
    try:
        await session.commit()
        await session.refresh(lot)
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )

    clear_yield_trend_cache()
    return {
        "status": "updated",
        "lot_id": lot_id,
        "data": update_data
    }


# Delete
@router.delete("/delete/{lot_id}")
@postgres_breaker
async def delete_lot(lot_id: str, session: AsyncSession = Depends(get_session)):
    lot = await session.get(Lot, lot_id)
    if not lot:
        raise HTTPException(404, f"{lot_id} not found")

    # 查是否有 yield_record 使用這個 lot_id
    try:
        result = await session.execute(select(YieldRecord).where(YieldRecord.lot_id == lot_id))
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )

    is_used = result.scalars().first() is not None

    if is_used:
        raise HTTPException(
            400,
            f"Cannot delete {lot_id}: It is referenced by yield_record"
        )
    try:
        await session.delete(lot)
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )
    try:
        await session.commit()
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )

    clear_yield_trend_cache()
    return {"status": "deleted", "lot_id": lot_id}

