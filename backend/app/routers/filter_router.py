# backend/app/routers/filter_router.py

from datetime import date
from typing import List

from aiobreaker import CircuitBreakerError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.common.circuit_breakers import postgres_breaker, circuit_open_counter
from app.database.database import get_session
from app.models.yield_record import YieldRecord
from app.models.lot import Lot

router = APIRouter(prefix="/filter", tags=["Filter"])


# ---- 1) 取得有資料的所有日期列表 ----
@postgres_breaker
@router.get("/dates", response_model=List[date])
async def list_dates(session: AsyncSession = Depends(get_session)):
    stmt = select(func.date(YieldRecord.timestamp)).distinct().order_by(
        func.date(YieldRecord.timestamp)
    )
    try:
        res = await session.execute(stmt)
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )
    return [row[0] for row in res.all()]


# ---- 2) 日期區間 -> 機台列表 ----
@postgres_breaker
@router.get("/machines", response_model=List[str])
async def list_machines(
    date_from: date, date_to: date, session: AsyncSession = Depends(get_session)
):
    # 先找該區間內的 lot_id
    sub = (
        select(YieldRecord.lot_id)
        .where(func.date(YieldRecord.timestamp) >= date_from)
        .where(func.date(YieldRecord.timestamp) <= date_to)
        .distinct()
        .subquery()
    )

    stmt = (
        select(Lot.station)
        .where(Lot.lot_id.in_(select(sub.c.lot_id)))
        .distinct()
        .order_by(Lot.station)
    )
    try:
        res = await session.execute(stmt)
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )
    return [row[0] for row in res.all()]


# ---- 3) 日期區間 + 機台 -> Recipe 列表 ----
@postgres_breaker
@router.get("/recipes", response_model=List[str])
async def list_recipes(
    date_from: date,
    date_to: date,
    station: str,
    session: AsyncSession = Depends(get_session),
):
    sub = (
        select(YieldRecord.lot_id)
        .where(func.date(YieldRecord.timestamp) >= date_from)
        .where(func.date(YieldRecord.timestamp) <= date_to)
        .distinct()
        .subquery()
    )

    stmt = (
        select(Lot.product)
        .where(Lot.lot_id.in_(select(sub.c.lot_id)))
        .where(Lot.station == station)
        .distinct()
        .order_by(Lot.product)
    )

    try:
        res = await session.execute(stmt)
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )
    return [row[0] for row in res.all()]


# ---- 4) 日期區間 + 機台 + Recipe -> Lot 列表 ----
@postgres_breaker
@router.get("/lots", response_model=List[str])
async def list_lots(
    date_from: date,
    date_to: date,
    station: str,
    product: str,
    session: AsyncSession = Depends(get_session),
):
    sub = (
        select(YieldRecord.lot_id)
        .where(func.date(YieldRecord.timestamp) >= date_from)
        .where(func.date(YieldRecord.timestamp) <= date_to)
        .distinct()
        .subquery()
    )

    stmt = (
        select(Lot.lot_id)
        .where(Lot.lot_id.in_(select(sub.c.lot_id)))
        .where(Lot.station == station)
        .where(Lot.product == product)
        .order_by(Lot.lot_id)
    )

    try:
        res = await session.execute(stmt)
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )
    return [row[0] for row in res.all()]
