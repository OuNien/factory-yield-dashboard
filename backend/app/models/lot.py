from sqlalchemy import Column, String, Integer

from .base import Base


class Lot(Base):
    __tablename__ = "lot"

    lot_id = Column(String, primary_key=True, index=True)
    product = Column(String)  # Recipe
    station = Column(String)  # 機台號

    total = Column(Integer)
    good = Column(Integer)
