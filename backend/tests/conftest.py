# backend/tests/conftest.py
import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.routers.auth_router import router as auth_router
from app.routers.user_router import router as user_router
from app.routers.lot_router import router as lot_router

from app.database.database import engine, AsyncSessionLocal
from app.models.base import Base
from app.models.user import User, Role
from app.auth.security import hash_password

import app.common.cache_key as cache_key


# ---- 避免 Redis clear cache 在測試時被真的執行 ----
@pytest.fixture(autouse=True)
def _patch_cache(monkeypatch):
    monkeypatch.setattr(cache_key, "clear_yield_trend_cache", lambda: None)


# ---- 建立資料庫（手動呼叫，不 autouse）----
@pytest.fixture(scope="session")
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


# ---- DB Session ----
@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


# ---- 建立 FastAPI app，並主動呼叫 prepare_database ----
@pytest.fixture(scope="session")
async def test_app(prepare_database):  # <-- 主動依賴 prepare_database
    app = FastAPI(title="Factory Dashboard Test API")

    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(lot_router)

    return app


# ---- http client ----
@pytest.fixture
async def client(test_app):
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


# ---- 測試用 admin 使用者 ----
@pytest.fixture
async def admin_user(db_session):
    username = "admin_test"
    password = "admin_pw"

    user = await db_session.get(User, username)
    if not user:
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=Role.admin,
        )
        db_session.add(user)
        await db_session.commit()

    yield {"obj": user, "password": password}

    # 測試結束後清除
    await db_session.delete(user)
    await db_session.commit()
