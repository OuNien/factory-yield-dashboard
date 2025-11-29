# app/models/user.py
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum as PyEnum

from .base import Base


class Role(str, PyEnum):
    viewer = "viewer"
    engineer = "engineer"
    admin = "admin"


class User(Base):
    __tablename__ = "user"

    username: Mapped[str] = mapped_column(String(50), primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role, name="role_enum"), nullable=False)
