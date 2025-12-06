import redis
from ..config.config import settings

redis_cache = redis.Redis.from_url(settings.REDIS_CACHE_URL)
redis_ratelimit = redis.Redis.from_url(settings.REDIS_RATELIMIT_URL)
