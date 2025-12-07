# app/routers/auth_router.py
from aiobreaker import CircuitBreakerError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.circuit_breakers import postgres_breaker, circuit_open_counter
from app.database.database import get_session
from app.auth.security import verify_password, create_access_token, get_current_user
from app.models.user import User, Role

router = APIRouter(prefix="/auth", tags=["Auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: Role

@postgres_breaker
@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    stmt = select(User).where(User.username == form_data.username)
    try:
        result = await session.execute(stmt)
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )

    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
        )

    token = create_access_token({"sub": user.username})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        username=user.username,
        role=user.role,
    )


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "role": current_user.role,
    }
