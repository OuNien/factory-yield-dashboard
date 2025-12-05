# backend/app/routers/yield_router.py

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_session
from app.database.mongo import mongo_db
from app.models.defect_summary import DefectSummary
from app.models.lot import Lot
from app.models.yield_record import YieldRecord

router = APIRouter(prefix="/yield", tags=["Yield & Trend"])


# ---- 原本的簡單列表 API（保留） ----
@router.get("/list")
async def list_yield(session: AsyncSession = Depends(get_session)):
    stmt = select(YieldRecord).order_by(YieldRecord.timestamp.desc())
    result = await session.execute(stmt)
    rows = result.scalars().all()

    return [
        {
            "id": r.id,
            "lot_id": r.lot_id,
            "total": r.total,
            "good": r.good,
            "yield_rate": r.yield_rate,
            "timestamp": r.timestamp,
        }
        for r in rows
    ]


# ---- 新：多天區間 + 機台 + Recipe + Lot IDs 的 Trend + Defect 資訊 ----
@router.get("/trend")
async def yield_trend(
    date_from: date,
    date_to: date,
    station: str,
    product: str,
    lots: List[str] = Query(),
    session: AsyncSession = Depends(get_session),
):
    # ---------------- 1) 依日期 / station / product / lot_ids 取得 yield ----------------
    stmt = (
        select(YieldRecord, Lot)
        .join(Lot, Lot.lot_id == YieldRecord.lot_id)
        .where(func.date(YieldRecord.timestamp) >= date_from)
        .where(func.date(YieldRecord.timestamp) <= date_to)
    )

    if station:
        stmt = stmt.where(Lot.station == station)
    if product:
        stmt = stmt.where(Lot.product == product)
    if lots:
        stmt = stmt.where(Lot.lot_id.in_(lots))
    print("@@@@@@", lots)
    result = await session.execute(stmt)
    rows = result.all()

    if not rows:
        return {
            "dates": [],
            "avg_yield": [],
            "defect_pareto": [],
            "defect_details": [],
        }

    # 用 rows 決定實際使用的 lot_ids（這裡不會包含額外 lot）
    used_lot_ids = sorted({r[0].lot_id for r in rows})

    # ---------------- 2) daily avg yield ----------------
    daily_map = {}
    for yr, _lot in rows:
        d_str = yr.timestamp.date().isoformat()
        daily_map.setdefault(d_str, []).append(float(yr.yield_rate))

    dates = sorted(daily_map.keys())
    avg_yield = [
        round(sum(vals) / len(vals), 2)
        for d, vals in sorted(daily_map.items())
    ]

    # ---------------- 3) Defect Summary（PostgreSQL） ----------------
    ds_stmt = select(DefectSummary).where(
        DefectSummary.lot_id.in_(lots if lots else used_lot_ids)
    )

    ds_rows = (await session.execute(ds_stmt)).scalars().all()

    pareto_map = {}
    for r in ds_rows:
        pareto_map[r.defect_type] = pareto_map.get(r.defect_type, 0) + r.count

    defect_pareto = [
        {"defect_type": k, "count": v}
        for k, v in pareto_map.items()
    ]
    defect_pareto.sort(key=lambda x: x["count"], reverse=True)

    # ---------------- 4) Mongo defect_detail ----------------
    lot_filter = lots if lots else used_lot_ids

    defect_details = []
    if lot_filter:
        coll = mongo_db["defect_detail"]
        mongo_docs = list(coll.find({"lot_id": {"$in": lot_filter}}))

        for d in mongo_docs:
            loc = d.get("location") or {}
            defect_details.append(
                {
                    "lot_id": d.get("lot_id"),
                    "defect_type": d.get("defect_type"),
                    "x": loc.get("x"),
                    "y": loc.get("y"),
                    "severity": d.get("severity"),
                    "wafer": d.get("wafer"),
                }
            )

    return {
        "dates": dates,
        "avg_yield": avg_yield,
        "defect_pareto": defect_pareto,
        "defect_details": defect_details,
    }

