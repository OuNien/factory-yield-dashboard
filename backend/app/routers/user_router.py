from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.auth.security import hash_password

from app.config.database import get_session

from app.models.user import User, Role

router = APIRouter(prefix="/user", tags=["User"])

class UserUpdate(BaseModel):
    password_hash: Optional[str] = None
    role: Optional[Role] = None

# Create
@router.post("/add")
async def create_user(username: str, password: str, role: Role,
    session: AsyncSession = Depends(get_session)):
    async with session.begin():
        # 檢查使用者是否存在
        result = await session.execute(
            select(User).where(User.username == username)
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
async def list_user(session: AsyncSession = Depends(get_session)):
    query = select(User)
    rows = (await session.execute(query)).scalars().all()
    return rows

@router.put("/update/{user_name}")
async def update_user(
    user_name: str,
    payload: UserUpdate,
    session: AsyncSession = Depends(get_session),
):
    # 1. 取得資料
    user = await session.get(User, user_name)
    if not user:
        raise HTTPException(404, f"{user_name} not found")

    # 2. 更新有傳入的欄位
    update_data = payload.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(user, key, value)
    setattr(user, "password_hash", hash_password(payload.password_hash))

    # 3. commit
    await session.commit()
    await session.refresh(user)

    return {
        "status": "updated",
        "lot_id": user_name,
        "data": update_data
    }


# Delete
@router.delete("/delete/{user_name}")
async def delete_user(user_name: str, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, user_name)
    if not user:
        raise HTTPException(404, f"{user_name} not found")

    await session.delete(user)
    await session.commit()

    return {"status": "deleted", "user_name": user_name}

