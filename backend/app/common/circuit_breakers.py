# app/common/circuit_breakers.py
import logging
from datetime import timedelta

from aiobreaker import CircuitBreaker
from prometheus_client import Counter

logger = logging.getLogger(__name__)

# Postgres 用的 breaker
postgres_breaker = CircuitBreaker(
    fail_max=5,  # 連續 5 次失敗就打開
    timeout_duration=timedelta(seconds=30),  # 30 秒後嘗試 half-open
    name="postgres_breaker",
)

# Mongo 用的 breaker
mongo_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=timedelta(seconds=30),
    name="mongo_breaker",
)

circuit_open_counter = Counter(
    "circuit_open_total",
    "Total times circuit breaker opened",
    ["name"]
)
