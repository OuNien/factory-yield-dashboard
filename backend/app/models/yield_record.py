from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey

from .base import Base


class YieldRecord(Base):
    __tablename__ = "yield_record"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lot_id = Column(String, ForeignKey("lot.lot_id"), index=True)
    good = Column(Integer)
    total = Column(Integer)
    yield_rate = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
