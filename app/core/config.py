from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tennisai"
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    REDIS_URL: str = "redis://localhost:6379/0"
    STORAGE_PATH: str = "./storage"
    AI_API_KEY: str = ""
    DEMO_MODE: bool = True
    CORS_ORIGINS: List[str] = ["*"]
    UPLOAD_MAX_SIZE_MB: int = 500
    ALLOWED_VIDEO_EXTENSIONS: List[str] = ["mp4", "mov", "webm", "avi", "zip"]
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
