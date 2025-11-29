# app/models/user.py
from sqlalchemy import Column, String, Enum
from app.models.base import Base
import enum


class Role(enum.Enum):
    viewer = "viewer"
    engineer = "engineer"
    admin = "admin"


class User(Base):
    __tablename__ = "user"

    username = Column(String, primary_key=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False)
