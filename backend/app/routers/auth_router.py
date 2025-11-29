# app/routers/auth_router.py
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_session
from app.models.user import User
from passlib.context import CryptContext
import jwt

from app.utils.auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginIn(BaseModel):
    username: str
    password: str


class LoginOut(BaseModel):
    access_token: str
    role: str


@router.post("/login", response_model=LoginOut)
async def login(payload: LoginIn, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(User).where(User.username == payload.username)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if not pwd_context.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password")

    token = jwt.encode(
        {
            "sub": user.username,
            "role": user.role.value,
            "exp": datetime.utcnow() + timedelta(hours=8),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    return LoginOut(access_token=token, role=user.role.value)
