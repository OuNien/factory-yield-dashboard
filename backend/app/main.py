# app/main.py
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.common.rate_limit import rate_limiter
from app.database.database import engine, get_session
from app.models.base import Base
from app.models.user import User
from app.routers.auth_router import router as auth_router
from app.routers.detail_router import router as detail_router
from app.routers.filter_router import router as filter_router
from app.routers.lot_router import router as lot_router
from app.routers.seed_router import router as seed_router
from app.routers.summary_router import router as summary_router
from app.routers.user_router import router as user_router
from app.routers.yield_router import router as yield_router
from app.services.redis_client import redis_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Factory Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發階段先全開
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    # 啟動時自動建表
    logger.info("Application starting up...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("🟢 PostgreSQL tables ensured.")
    logger.info("Application startup finished")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Application shutting down...")


# 掛上各個 router
app.include_router(auth_router)
app.include_router(lot_router)
app.include_router(yield_router)
app.include_router(summary_router)
app.include_router(detail_router)
app.include_router(filter_router)
app.include_router(seed_router)
app.include_router(user_router)


@app.get("/health")
async def health():
    logger.info("Application health...")
    return {"status": "ok"}


@app.get("/health/db")
async def healthz_db(session: AsyncSession = Depends(get_session)):
    try:
        query = select(User)
        await session.execute(query)
        return {"status": "ok", "db": "ok"}
    except:
        return {"status": "error", "db": "error"}


@app.get("/health/redis")
async def redis_health():
    try:
        redis_client.ping()
        return {"redis": "ok"}
    except:
        return {"redis": "down"}


@app.middleware("http")
async def global_rate_limit(request: Request, call_next):
    path = request.url.path
    logger.info("Application global_rate_limit...")
    # 你可以排除 health check
    if path.startswith("/health"):
        return await call_next(request)

    client_ip = request.client.host
    key = f"ip:{client_ip}:{path}"

    try:
        rate_limiter(key, max_tokens=5, refill_rate=1.0)
        logger.info(f"Application global_rate_limit {key}...")
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

    return await call_next(request)
