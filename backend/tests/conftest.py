import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database import get_db
from app.main import app


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Create a scoped database session with NullPool for testing."""
    test_engine = create_async_engine(settings.database_url, poolclass=NullPool)
    test_session_local = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with test_session_local() as session:
        yield session
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session):
    """Async test client with overridden database dependency."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
