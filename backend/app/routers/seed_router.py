# app/routers/seed_router.py
import random
from datetime import datetime, timedelta, date

from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache_key import clear_yield_trend_cache
from app.database.database import get_session
from app.database.mongo import mongo_db
from app.models.lot import Lot
from app.models.yield_record import YieldRecord
from app.models.defect_summary import DefectSummary
from app.auth.security import require_role


router = APIRouter(prefix="/seed", tags=["Seed / 測試資料"])

MACHINES = ["AOI-01", "AOI-02", "AOI-03"]
RECIPES = ["PKG-A", "PKG-B", "PKG-C"]
DEFECT_TYPES = ["Scratch", "Particle", "Bridge", "Crack"]


@router.get("/sql", dependencies=[Depends(require_role(["admin"]))])
async def seed_sql(session: AsyncSession = Depends(get_session)):
    # 1) 清空 SQL
    await session.execute(delete(DefectSummary))
    await session.execute(delete(YieldRecord))
    await session.execute(delete(Lot))
    await session.commit()

    # 2) 清空 Mongo
    coll = mongo_db["defect_detail"]
    coll.delete_many({})

    lots_to_insert = []
    yield_to_insert = []
    summary_to_insert = []
    defect_docs = []

    today = date.today()
    base_date = today - timedelta(days=6)  # 最近 7 天
    lot_index = 1000

    for d_offset in range(7):
        cur_date = base_date + timedelta(days=d_offset)
        for machine in MACHINES:
            for recipe in RECIPES:
                # 每個 machine/recipe 每天隨機 1~3 lot
                for _ in range(random.randint(1, 3)):
                    lot_id = f"LOT{lot_index:05d}"
                    lot_index += 1

                    total = random.randint(500, 1200)
                    # 製造一個合理的總缺陷數
                    total_defect = random.randint(0, int(total * 0.2))
                    good = total - total_defect
                    yield_rate = round(good / total * 100, 2) if total > 0 else 0

                    lots_to_insert.append(
                        Lot(
                            lot_id=lot_id,
                            product=recipe,
                            station=machine,
                            total=total,
                            good=good,
                        )
                    )

                    # timestamp 一律放當天中午
                    ts = datetime.combine(cur_date, datetime.min.time()) + timedelta(
                        hours=12
                    )

                    yield_to_insert.append(
                        YieldRecord(
                            lot_id=lot_id,
                            total=total,
                            good=good,
                            yield_rate=yield_rate,
                            timestamp=ts,
                        )
                    )

                    # 把 total_defect 分配到不同 defect_type
                    remain = total_defect
                    for defect_type in DEFECT_TYPES:
                        if remain <= 0:
                            count = 0
                        else:
                            # 隨機切一個份額
                            count = random.randint(0, remain)
                        remain -= count

                        if count <= 0:
                            continue

                        summary_to_insert.append(
                            DefectSummary(
                                lot_id=lot_id,
                                defect_type=defect_type,
                                count=count,
                            )
                        )

                        # Mongo 只放一小部分點 (最多 50 點)，避免太大
                        sample_count = min(count, 50)
                        for _ in range(sample_count):
                            defect_docs.append(
                                {
                                    "lot_id": lot_id,
                                    "defect_type": defect_type,
                                    "location": {
                                        "x": round(random.uniform(0, 100), 2),
                                        "y": round(random.uniform(0, 100), 2),
                                    },
                                    "severity": random.choice(["L", "M", "H"]),
                                    "wafer": random.randint(1, 25),
                                    "image_path": None,
                                    "extra": {},
                                }
                            )

    # 3) 先插 Lot，確保 FK 存在
    session.add_all(lots_to_insert)
    await session.commit()

    # 4) 再插 Yield + Summary
    session.add_all(yield_to_insert)
    session.add_all(summary_to_insert)
    await session.commit()

    # 5) Mongo insert_many
    if defect_docs:
        coll.insert_many(defect_docs)
    clear_yield_trend_cache()
    return {
        "status": "ok",
        "lot_count": len(lots_to_insert),
        "yield_count": len(yield_to_insert),
        "defect_summary_count": len(summary_to_insert),
        "defect_detail_count": len(defect_docs),
    }
