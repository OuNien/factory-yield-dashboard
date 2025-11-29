from sqlalchemy import Column, String, Integer, ForeignKey

from .base import Base


class DefectSummary(Base):
    __tablename__ = "defect_summary"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lot_id = Column(String, ForeignKey("lot.lot_id"), index=True)
    defect_type = Column(String)
    count = Column(Integer)
