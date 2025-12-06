# app/routers/task_router.py
from celery.result import AsyncResult
from fastapi import APIRouter
from pydantic import BaseModel

from app.common.celery_app import celery_app
from app.common.tasks import recalc_yield_for_lots

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class RecalcRequest(BaseModel):
    lots: list[str]


@router.post("/recalc_yield")
async def enqueue_recalc(req: RecalcRequest):
    """
    丟非同步工作給 Celery worker：
    - 回傳 task_id，之後可以設計 /tasks/status/{task_id} 來查狀態。
    """
    async_result = recalc_yield_for_lots.delay(req.lots)
    return {
        "task_id": async_result.id,
        "status": "queued",
    }


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    res = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "state": res.state,
        "result": res.result if res.successful() else None,
    }
