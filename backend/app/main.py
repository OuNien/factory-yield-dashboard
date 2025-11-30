# app/main.py
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.database import engine
from app.models.base import Base
from app.routers.auth_router import router as auth_router
from app.routers.detail_router import router as detail_router
from app.routers.filter_router import router as filter_router
from app.routers.lot_router import router as lot_router
from app.routers.seed_router import router as seed_router
from app.routers.summary_router import router as summary_router
from app.routers.yield_router import router as yield_router
from app.routers.user_router import router as user_router

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
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("🟢 PostgreSQL tables ensured.")


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
    return {"status": "ok"}
