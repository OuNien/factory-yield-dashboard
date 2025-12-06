import hashlib
import json

from app.services.redis_client import redis_client


def make_cache_key(prefix: str, params: dict):
    # params 要排序，否則兩個 dict 順序不同會造成不同 key
    raw = json.dumps(params, sort_keys=True)
    h = hashlib.sha1(raw.encode()).hexdigest()
    return f"{prefix}:{h}"


def clear_yield_trend_cache():
    keys = redis_client.keys("yield_trend:*")
    if keys:
        redis_client.delete(*keys)
        print(f"🧹 Cleared {len(keys)} trend cache keys")
