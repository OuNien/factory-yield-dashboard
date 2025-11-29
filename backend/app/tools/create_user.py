# tools/create_user.py

import asyncio
from sqlalchemy import select
from passlib.context import CryptContext

from app.config.database import AsyncSessionLocal
from app.models.user import User, Role


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_user(username: str, password: str, role: Role):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 檢查使用者是否存在
            result = await session.execute(
                select(User).where(User.username == username)
            )
            exists = result.scalars().first()

            if exists:
                print(f"❗ User '{username}' already exists.")
                return

            user = User(
                username=username,
                password_hash=pwd_context.hash(password),
                role=role,
            )
            session.add(user)

        print(f"✅ User created: {username} ({role.value})")


async def main():
    # 你可以依需求建立多個帳號
    await create_user("admin", "admin", Role.admin)
    await create_user("eng", "eng", Role.engineer)
    await create_user("op", "op", Role.viewer)


if __name__ == "__main__":
    asyncio.run(main())
