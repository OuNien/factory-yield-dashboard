# app/database.py
from pydantic import BaseSettings




class Settings(BaseSettings):
    database_url: str
    mongo_url: str
    mongo_db: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    redis_expire_seconds = 30  # 30 秒快取
    REDIS_CACHE_URL: str
    REDIS_RATELIMIT_URL: str
    REDIS_BROKER_URL: str
    REDIS_BACKEND_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
