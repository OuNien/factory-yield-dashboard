# app/database.py
from pydantic import BaseSettings




class Settings(BaseSettings):
    database_url: str
    mongo_url: str
    mongo_db: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    class Config:
        env_file = ".env"


settings = Settings()
