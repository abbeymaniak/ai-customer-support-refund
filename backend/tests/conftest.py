import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database import get_db
from app.main import app
from app.models.auth import AdminUser
from app.services.auth_service import AuthService


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
    """Async test client with overridden database dependency (unauthenticated)."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def admin_auth_client(db_session):
    """Async test client authenticated as an administrator."""
    stmt = select(AdminUser).where(AdminUser.email == "admin@store.com")
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        user = AdminUser(
            id=uuid.uuid4(),
            email="admin@store.com",
            password_hash=AuthService.hash_password("admin123"),
            name="Store Administrator",
            role="admin",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

    token = AuthService.create_access_token(user)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    cookies = {"access_token": token}
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def agent_auth_client(db_session):
    """Async test client authenticated as a support agent."""
    stmt = select(AdminUser).where(AdminUser.email == "lead@store.com")
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        user = AdminUser(
            id=uuid.uuid4(),
            email="lead@store.com",
            password_hash=AuthService.hash_password("lead123"),
            name="Support Lead",
            role="agent",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

    token = AuthService.create_access_token(user)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    cookies = {"access_token": token}
    async with AsyncClient(transport=transport, base_url="http://test", cookies=cookies) as client:
        yield client
    app.dependency_overrides.clear()
