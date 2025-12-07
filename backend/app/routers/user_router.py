from aiobreaker import CircuitBreakerError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from starlette import status

from app.auth.security import hash_password
from app.common.circuit_breakers import postgres_breaker, circuit_open_counter

from app.database.database import get_session

from app.models.user import User, Role

router = APIRouter(prefix="/user", tags=["User"])

class UserUpdate(BaseModel):
    password_hash: Optional[str] = None
    role: Optional[Role] = None

# Create
@router.post("/add")
@postgres_breaker
async def create_user(username: str, password: str, role: Role,
    session: AsyncSession = Depends(get_session)):
    async with session.begin():
        # 檢查使用者是否存在
        try:
            result = await session.execute(
                select(User).where(User.username == username)
            )
        except CircuitBreakerError:
            circuit_open_counter.labels(name="postgres_breaker").inc()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database temporarily unavailable (circuit open)."
            )

        exists = result.scalars().first()

        if exists:
            raise HTTPException(400, f"username {username} already exists")

        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
        )
        session.add(user)

    print(f"✅ User created: {username} ({role.value})")
    return {"status": "ok"}


# Read All
@router.get("/list")
@postgres_breaker
async def list_user(session: AsyncSession = Depends(get_session)):
    query = select(User)
    try:
        rows = (await session.execute(query)).scalars().all()
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )

    return rows

@router.put("/update/{user_name}")
@postgres_breaker
async def update_user(
    user_name: str,
    payload: UserUpdate,
    session: AsyncSession = Depends(get_session),
):
    # 1. 取得資料
    try:
        user = await session.get(User, user_name)
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )

    if not user:
        raise HTTPException(404, f"{user_name} not found")

    # 2. 更新有傳入的欄位
    update_data = payload.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(user, key, value)
    setattr(user, "password_hash", hash_password(payload.password_hash))

    # 3. commit
    try:
        await session.commit()
        await session.refresh(user)
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )

    return {
        "status": "updated",
        "lot_id": user_name,
        "data": update_data
    }


# Delete
@router.delete("/delete/{user_name}")
@postgres_breaker
async def delete_user(user_name: str, session: AsyncSession = Depends(get_session)):
    try:
        user = await session.get(User, user_name)
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )

    if not user:
        raise HTTPException(404, f"{user_name} not found")

    try:
        await session.delete(user)
        await session.commit()
    except CircuitBreakerError:
        circuit_open_counter.labels(name="postgres_breaker").inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database temporarily unavailable (circuit open)."
        )

    return {"status": "deleted", "user_name": user_name}

