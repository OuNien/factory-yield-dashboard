# app/celery_app.py
import os
from celery import Celery

from app.config.config import settings

# 在 docker-compose 裡 redis service 名稱就是 "redis"
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


celery_app = Celery(
    "factory_yield",
    broker=settings.REDIS_BROKER_URL,
    backend=settings.REDIS_BACKEND_URL,
)

# 自動載入 tasks
celery_app.autodiscover_tasks(["app.common.tasks"])
