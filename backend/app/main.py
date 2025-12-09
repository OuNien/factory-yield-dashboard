# app/main.py
import logging
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.common.db_tracing import setup_sqlalchemy_tracing
from app.common.rate_limit import rate_limiter
from app.common.tracing import setup_tracing
from app.database.database import engine, get_session
from app.models.base import Base
from app.models.user import User, Role
from app.routers.auth_router import router as auth_router
from app.routers.detail_router import router as detail_router
from app.routers.filter_router import router as filter_router
from app.routers.lot_router import router as lot_router
from app.routers.seed_router import router as seed_router
from app.routers.summary_router import router as summary_router
from app.routers.task_router import router as task_router
from app.routers.user_router import router as user_router
from app.routers.yield_router import router as yield_router
from app.services.redis_client import redis_ratelimit
from app.tools.create_user import create_user

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)

load_dotenv()

import os

DISABLE_TRACING = os.getenv("DISABLE_TRACING", "false").lower() == "true"

app = FastAPI(title="Factory Dashboard API")

origins = [
    "https://factory-yield-dashboard-front.onrender.com",
    "https://factory-yield-dashboard.onrender.com",
    "http://localhost:8080",   # optional for local debug
]



# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # 開發階段先全開
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.on_event("startup")
async def on_startup():
    logger.info("Application starting up...")

    if not DISABLE_TRACING:
        setup_tracing("factory-backend")
        FastAPIInstrumentor().instrument_app(app)
        RedisInstrumentor().instrument()
        setup_sqlalchemy_tracing(engine)
    else:
        logger.info("Tracing disabled on this environment.")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        await create_user("admin", "admin", Role.admin)
        await create_user("eng", "eng", Role.engineer)
        await create_user("op", "op", Role.viewer)



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
app.include_router(task_router)


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
        redis_ratelimit.ping()
        return {"redis_ratelimit": "ok"}
    except:
        return {"redis_ratelimit": "down"}


if not os.getenv("DISABLE_REDIS", "false").lower() == "true":
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
            rate_limiter(key, max_tokens=100000, refill_rate=100000)
            logger.info(f"Application global_rate_limit {key}...")
        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

        return await call_next(request)
else:
    logger.info("Rate limiter disabled.")

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start = time.time()

    response = await call_next(request)

    process_time = time.time() - start
    endpoint = request.url.path

    REQUEST_LATENCY.labels(endpoint=endpoint).observe(process_time)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        http_status=response.status_code
    ).inc()

    return response


REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency",
    ["endpoint"]
)


@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(data, media_type=CONTENT_TYPE_LATEST)
