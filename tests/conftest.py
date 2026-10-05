import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.database import Base
from fastapi.testclient import TestClient
from app.main import app

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

@pytest_asyncio.fixture(autouse=True)
async def db_schema():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def client():
    return TestClient(app)
