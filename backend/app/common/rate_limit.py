import time

from fastapi import HTTPException

from app.services.redis_client import redis_client


def rate_limiter(
    key: str,
    max_tokens: int = 10,
    refill_rate: float = 1.0,
):
    pipe = redis_client.pipeline()
    now = time.time()

    pipe.hgetall(key)
    data = pipe.execute()[0]

    if not data:
        # 初始化
        redis_client.hset(key, mapping={
            "tokens": max_tokens - 1,
            "timestamp": now
        })
        return

    # 同時支援 bytes / str
    tokens = float(data.get("tokens") or data.get(b"tokens") or 0)
    last_ts = float(data.get("timestamp") or data.get(b"timestamp") or 0)

    # 補充 token
    delta = now - last_ts
    tokens = min(max_tokens, tokens + delta * refill_rate)

    if tokens < 1:
        raise HTTPException(429, "Too Many Requests")

    tokens -= 1

    redis_client.hset(key, mapping={
        "tokens": tokens,
        "timestamp": now
    })
