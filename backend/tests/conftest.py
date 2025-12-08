# backend/tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.base import Base
from app.database.database import get_session as real_get_session


# ==============================
#   測試用 SQLite 資料庫
# ==============================
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ==============================
#   覆寫 get_session (FastAPI DI)
# ==============================
async def override_get_session() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session


# ==============================
#   Dummy Redis / Mongo
# ==============================

class DummyPipeline:
    def __init__(self, store: dict):
        self.store = store
        self.ops = []

    def hgetall(self, key: str):
        self.ops.append(("hgetall", key))
        return self

    def execute(self):
        results = []
        for op, key in self.ops:
            if op == "hgetall":
                results.append(self.store.get(key, {}))
        self.ops.clear()
        return results


class DummyRedis:
    def __init__(self):
        self.store: dict = {}

    # health check 用
    def ping(self):
        return True

    # rate_limit 用
    def pipeline(self):
        return DummyPipeline(self.store)

    def hset(self, key: str, mapping: dict):
        self.store[key] = mapping

    # cache_key 用
    def keys(self, pattern="*"):
        return list(self.store.keys())

    def delete(self, *keys):
        for k in keys:
            self.store.pop(k, None)

    # 一般 get/set
    def get(self, key: str):
        return self.store.get(key)

    def set(self, key: str, value, ex=None):
        self.store[key] = value
        return True


class DummyCollection:
    def __init__(self):
        self.docs = []

    def find(self, *args, **kwargs):
        # 回傳 list，就像 list(mongo_db["xxx"].find())
        return list(self.docs)

    def insert_many(self, docs):
        self.docs.extend(docs)
        return True

    def insert_one(self, doc):
        self.docs.append(doc)
        return True

    def delete_many(self, *args, **kwargs):
        self.docs.clear()
        return True

    def aggregate(self, pipeline):
        # 測試階段先回空，之後要真的驗證再加行為
        return []


class DummyMongoDB:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name: str):
        if name not in self.collections:
            self.collections[name] = DummyCollection()
        return self.collections[name]


def mock_redis_and_mongo():
    """把專案裡用到的 Redis / Mongo 全部換成 Dummy 版本。"""
    from app.services import redis_client
    from app.common import rate_limit, cache_key
    from app.database import mongo as mongo_module
    from app.routers import detail_router, seed_router, yield_router

    dummy_redis = DummyRedis()
    dummy_mongo = DummyMongoDB()

    # 1) redis_client 自己的實例
    redis_client.redis_cache = dummy_redis
    redis_client.redis_ratelimit = dummy_redis

    # 2) rate_limit 模組中引用的 redis_ratelimit
    rate_limit.redis_ratelimit = dummy_redis

    # 3) cache_key 模組中引用的 redis_cache
    cache_key.redis_cache = dummy_redis

    # 4) yield_router 裡 import 的 redis_cache / mongo_db
    yield_router.redis_cache = dummy_redis
    yield_router.mongo_db = dummy_mongo

    # 5) detail_router / seed_router 裡 import 的 mongo_db
    detail_router.mongo_db = dummy_mongo
    seed_router.mongo_db = dummy_mongo

    # 6) database.mongo 裡的 mongo_db（有些地方直接用這個）
    mongo_module.mongo_db = dummy_mongo


# ==============================
#   建 Table / 摧 Table
# ==============================
@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ==============================
#   共用 HTTP client
# ==============================
@pytest.fixture
async def client():
    # 覆寫 DB Session
    app.dependency_overrides[real_get_session] = override_get_session

    # Mock Redis / Mongo，避免真的去連外部服務
    mock_redis_and_mongo()

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
