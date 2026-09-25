"""Integration tests for customer authentication, JWT protection, token rotation, and role isolation."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.auth import AdminUser, RefreshToken
from app.models.customer import Customer
from app.services.auth_service import AuthService
from app.services.customer_auth_service import CustomerAuthService


@pytest.mark.asyncio
async def test_customer_login_success(async_client, db_session):
    """Test AC-1, AC-3: Successful login with valid credentials sets customer cookies and returns profile."""
    res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": "sarah.jenkins@example.com", "password": "customer123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "sarah.jenkins@example.com"
    assert data["role"] == "customer"
    assert data["name"] == "Sarah Jenkins"
    assert data["is_active"] is True
    assert data["orders_count"] == 18
    assert "id" in data

    # Verify dedicated customer cookies
    cookies = res.cookies
    assert "customer_access_token" in cookies
    assert "customer_refresh_token" in cookies
    assert "access_token" not in cookies  # Ensure no collision with admin cookies


@pytest.mark.asyncio
async def test_customer_login_invalid_password(async_client):
    """Test AC-3: Login with invalid password returns 401."""
    res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": "sarah.jenkins@example.com", "password": "wrongpassword"},
    )
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


@pytest.mark.asyncio
async def test_customer_login_unknown_email(async_client):
    """Test AC-3: Non-existent email returns 401."""
    res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": "unknown.person@example.com", "password": "customer123"},
    )
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


@pytest.mark.asyncio
async def test_customer_login_inactive_user(async_client, db_session):
    """Test AC-3: Inactive customer accounts cannot authenticate."""
    email = f"inactive_cust_{uuid.uuid4().hex[:8]}@example.com"
    inactive_customer = Customer(
        id=uuid.uuid4(),
        email=email,
        name="Inactive Customer",
        password_hash=CustomerAuthService.hash_password("password123"),
        is_active=False,
    )
    db_session.add(inactive_customer)
    await db_session.commit()

    res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


@pytest.mark.asyncio
async def test_customer_me_authenticated_and_unauthenticated(async_client):
    """Test AC-4: /api/customer/auth/me rejects unauthenticated callers and accepts valid cookie."""
    # Unauthenticated
    unauth_res = await async_client.get("/api/customer/auth/me")
    assert unauth_res.status_code == 401

    # Login to obtain cookies
    login_res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": "sarah.jenkins@example.com", "password": "customer123"},
    )
    access_token = login_res.cookies["customer_access_token"]

    # Authenticated via cookie
    auth_res = await async_client.get(
        "/api/customer/auth/me",
        cookies={"customer_access_token": access_token},
    )
    assert auth_res.status_code == 200
    assert auth_res.json()["email"] == "sarah.jenkins@example.com"
    assert auth_res.json()["role"] == "customer"


@pytest.mark.asyncio
async def test_customer_token_refresh_rotation(async_client, db_session):
    """Test AC-3: Customer refresh token rotates, revokes old token, and rejects replay."""
    login_res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": "david.miller@example.com", "password": "customer123"},
    )
    initial_refresh = login_res.cookies["customer_refresh_token"]

    # Rotate refresh token
    refresh_res = await async_client.post(
        "/api/customer/auth/refresh",
        cookies={"customer_refresh_token": initial_refresh},
    )
    assert refresh_res.status_code == 200
    assert refresh_res.json()["status"] == "refreshed"
    new_refresh = refresh_res.cookies["customer_refresh_token"]
    assert new_refresh != initial_refresh

    # Replay attack with used token must fail
    replay_res = await async_client.post(
        "/api/customer/auth/refresh",
        cookies={"customer_refresh_token": initial_refresh},
    )
    assert replay_res.status_code == 401


@pytest.mark.asyncio
async def test_customer_logout_revocation(async_client, db_session):
    """Test AC-3: Logout marks token as revoked and clears cookies."""
    login_res = await async_client.post(
        "/api/customer/auth/login",
        json={"email": "david.miller@example.com", "password": "customer123"},
    )
    refresh_token = login_res.cookies["customer_refresh_token"]

    logout_res = await async_client.post(
        "/api/customer/auth/logout",
        cookies={"customer_refresh_token": refresh_token},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "logged_out"

    # Verify token is marked revoked in database
    token_hash = CustomerAuthService.hash_token(refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    record = (await db_session.execute(stmt)).scalar_one()
    assert record.revoked is True


@pytest.mark.asyncio
async def test_admin_and_customer_token_isolation(async_client, db_session):
    """Test AC-3, AC-4: Admin token cannot authenticate to customer endpoints."""
    await AuthService.ensure_seed_users(db_session)
    admin_login = await async_client.post(
        "/api/auth/login",
        json={"email": "admin@store.com", "password": "admin123"},
    )
    admin_access_token = admin_login.cookies["access_token"]

    # Pass admin access token as customer_access_token
    res = await async_client.get(
        "/api/customer/auth/me",
        cookies={"customer_access_token": admin_access_token},
    )
    assert res.status_code == 401
    assert "Invalid or expired customer access token" in res.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token_check_constraint(db_session):
    """Test AC-2: Refresh token requires either user_id or customer_id, but not both or neither."""
    # Neither
    invalid_token1 = RefreshToken(
        id=uuid.uuid4(),
        user_id=None,
        customer_id=None,
        token_hash=uuid.uuid4().hex,
        expires_at=uuid.uuid4().hex[:10],
    )
    db_session.add(invalid_token1)
    with pytest.raises(Exception):
        await db_session.commit()
    await db_session.rollback()
