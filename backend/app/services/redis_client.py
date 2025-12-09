import redis
from ..config.config import settings




import os
import redis

USE_FAKE_REDIS = os.getenv("DISABLE_REDIS", "false").lower() == "true"

if USE_FAKE_REDIS:
    class FakeRedis:
        def pipeline(self):
            return self
        def hgetall(self, *a, **k):
            return {}
        def hset(self, *a, **k):
            return True
        def execute(self):
            return [{}]
        def ping(self):
            return True
        def keys(self, *a, **k):
            return {}

    redis_cache = FakeRedis()
    redis_ratelimit = FakeRedis()

else:
    redis_cache = redis.Redis.from_url(settings.REDIS_CACHE_URL)
    redis_ratelimit = redis.Redis.from_url(settings.REDIS_RATELIMIT_URL)
