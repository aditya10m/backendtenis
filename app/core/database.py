import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

Base = declarative_base()

def get_database_url() -> str:
    url = settings.DATABASE_URL
    # If using default localhost postgres on Render (where localhost:5432 doesn't exist),
    # seamlessly fall back to local sqlite file so app never throws 500
    if not url or "localhost:5432" in url or "127.0.0.1:5432" in url:
        sqlite_path = os.path.join(settings.STORAGE_PATH, "badminton.db")
        return f"sqlite+aiosqlite:///{sqlite_path}"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

DB_URL = get_database_url()
logger.info(f"Connecting to database: {DB_URL.split('@')[-1] if '@' in DB_URL else DB_URL}")

engine = create_async_engine(DB_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_models():
    """Create all database tables automatically on startup."""
    import app.models  # ensure models are registered with Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
