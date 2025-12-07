# app/auth/security.py
from datetime import datetime, timedelta
from typing import Optional, List

import jwt
from aiobreaker import CircuitBreakerError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_session
from app.models.user import User, Role
from ..common.circuit_breakers import postgres_breaker, circuit_open_counter
from ..config.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# 使用 PBKDF2-SHA256 —— 最穩定、無依賴、無 bcrypt 問題
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    """產生安全的雜湊密碼"""
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """驗證密碼是否正確"""
    return pwd_context.verify(password, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

@postgres_breaker
async def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    stmt = select(User).where(User.username == username)
    try:
        result = await session.execute(stmt)
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


def require_role(roles: List[Role]):
    async def wrapper(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient privileges",
            )
        return user

    return wrapper
