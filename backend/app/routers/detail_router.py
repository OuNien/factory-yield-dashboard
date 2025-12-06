from typing import Optional, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from app.common.cache_key import clear_yield_trend_cache
from app.database.mongo import mongo_db

router = APIRouter(prefix="/detail", tags=["Defect Detail (Mongo)"])


# --------- Pydantic Schema（放在 router 裡） ---------

class Location(BaseModel):
    x: float
    y: float


class DefectDetailIn(BaseModel):
    lot_id: str
    defect_type: str
    location: Location
    wafer: Optional[int] = None
    severity: Optional[str] = None
    image_path: Optional[str] = None
    extra: Optional[Dict] = None


class DefectDetailOut(DefectDetailIn):
    id: str


# --------- API ---------

@router.post("/add", response_model=DefectDetailOut)
async def add_detail(data: DefectDetailIn):
    doc = data.dict()
    result = mongo_db["defect_detail"].insert_one(doc)
    clear_yield_trend_cache()

    return DefectDetailOut(
        id=str(result.inserted_id),
        **data.dict()
    )


@router.get("/by_lot", response_model=list[DefectDetailOut])
async def get_by_lot(lot_id: str):
    docs = list(mongo_db["defect_detail"].find({"lot_id": lot_id}))

    out = []
    for d in docs:
        d["id"] = str(d.pop("_id"))
        out.append(DefectDetailOut(**d))

    return out

@router.get("/list", response_model=list[DefectDetailOut])
async def get_by_lot():
    docs = list(mongo_db["defect_detail"].find())

    out = []
    for d in docs:
        d["id"] = str(d.pop("_id"))
        out.append(DefectDetailOut(**d))

    return out