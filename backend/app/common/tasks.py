# app/tasks.py
from datetime import datetime
from time import sleep

from .celery_app import celery_app


@celery_app.task
def recalc_yield_for_lots(lot_ids: list[str]) -> dict:
    """
    Demo：非同步重算某些 lots 的統計數據。
    這裡先做假裝運算 (sleep)，實務上你可以去 PostgreSQL + Mongo 抓資料重算。
    """
    # 模擬重運算
    sleep(5)

    # 這裡先回傳簡化結果，面試講解時可以說「實際會去重算 yiled、缺陷 Pareto 等」
    return {
        "lots": lot_ids,
        "status": "recalculated",
        "finished_at": datetime.utcnow().isoformat() + "Z",
    }
