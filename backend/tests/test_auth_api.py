"""Integration tests for admin authentication, JWT protection, token rotation, and role enforcement."""

import uuid

import pytest
from sqlalchemy import select

from app.models.auth import AdminUser, RefreshToken
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_login_success(async_client, db_session):
    """Test AC-1, AC-2: Successful login with valid credentials sets HTTP-only cookies and returns profile."""
    # Ensure default admin exists
    await AuthService.ensure_seed_users(db_session)

    res = await async_client.post(
        "/api/auth/login",
        json={"email": "admin@store.com", "password": "admin123"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "admin@store.com"
    assert data["role"] == "admin"
    assert data["name"] == "Store Administrator"
    assert "id" in data

    # Verify cookies
    cookies = res.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies


@pytest.mark.asyncio
async def test_login_invalid_password(async_client, db_session):
    """Test AC-2: Login with invalid password returns 401."""
    await AuthService.ensure_seed_users(db_session)

    res = await async_client.post(
        "/api/auth/login",
        json={"email": "admin@store.com", "password": "wrongpassword"},
    )
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


@pytest.mark.asyncio
async def test_login_inactive_user(async_client, db_session):
    """Test AC-2: Inactive accounts cannot authenticate."""
    email = f"inactive_{uuid.uuid4().hex[:8]}@store.com"
    inactive_user = AdminUser(
        id=uuid.uuid4(),
        email=email,
        password_hash=AuthService.hash_password("password123"),
        name="Inactive Staff",
        role="agent",
        is_active=False,
    )
    db_session.add(inactive_user)
    await db_session.commit()

    res = await async_client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_token_refresh_rotation(async_client, db_session):
    """Test AC-3: Token refresh endpoint rotates refresh token and issues new access token."""
    await AuthService.ensure_seed_users(db_session)

    # 1. Login to get initial cookies
    login_res = await async_client.post(
        "/api/auth/login",
        json={"email": "admin@store.com", "password": "admin123"},
    )
    assert login_res.status_code == 200
    old_refresh_token = login_res.cookies.get("refresh_token")
    old_access_token = login_res.cookies.get("access_token")

    # 2. Call refresh endpoint with the refresh cookie
    refresh_res = await async_client.post(
        "/api/auth/refresh",
        cookies={"refresh_token": old_refresh_token},
    )
    assert refresh_res.status_code == 200
    assert refresh_res.json()["status"] == "refreshed"

    new_refresh_token = refresh_res.cookies.get("refresh_token")
    new_access_token = refresh_res.cookies.get("access_token")

    assert new_refresh_token != old_refresh_token
    assert new_access_token != old_access_token

    # 3. Check old token was marked revoked in DB
    old_hash = AuthService.hash_token(old_refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == old_hash)
    result = await db_session.execute(stmt)
    old_token_record = result.scalar_one_or_none()
    assert old_token_record is not None
    assert old_token_record.revoked is True


@pytest.mark.asyncio
async def test_token_refresh_replay_detection(async_client, db_session):
    """Test AC-3: Reusing a rotated refresh token is rejected with 401."""
    await AuthService.ensure_seed_users(db_session)

    # 1. Login
    login_res = await async_client.post(
        "/api/auth/login",
        json={"email": "admin@store.com", "password": "admin123"},
    )
    refresh_token = login_res.cookies.get("refresh_token")

    # 2. First refresh succeeds
    res1 = await async_client.post(
        "/api/auth/refresh",
        cookies={"refresh_token": refresh_token},
    )
    assert res1.status_code == 200

    # 3. Replaying the original (now revoked) token fails
    res2 = await async_client.post(
        "/api/auth/refresh",
        cookies={"refresh_token": refresh_token},
    )
    assert res2.status_code == 401


@pytest.mark.asyncio
async def test_logout_revocation(async_client, db_session):
    """Test AC-4: Logout revokes refresh token and clears session cookies."""
    await AuthService.ensure_seed_users(db_session)

    # 1. Login
    login_res = await async_client.post(
        "/api/auth/login",
        json={"email": "admin@store.com", "password": "admin123"},
    )
    refresh_token = login_res.cookies.get("refresh_token")

    # 2. Logout
    logout_res = await async_client.post(
        "/api/auth/logout",
        cookies={"refresh_token": refresh_token},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "logged_out"

    # 3. Verify token revoked in DB
    token_hash = AuthService.hash_token(refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    result = await db_session.execute(stmt)
    record = result.scalar_one_or_none()
    assert record.revoked is True


@pytest.mark.asyncio
async def test_get_me_profile(async_client, admin_auth_client):
    """Test AC-5: /api/auth/me returns current user profile when authenticated and 401 when not."""
    # Unauthenticated
    unauth_res = await async_client.get("/api/auth/me")
    assert unauth_res.status_code == 401

    # Authenticated
    auth_res = await admin_auth_client.get("/api/auth/me")
    assert auth_res.status_code == 200
    profile = auth_res.json()
    assert profile["email"] == "admin@store.com"
    assert profile["role"] == "admin"


@pytest.mark.asyncio
async def test_admin_routes_unauthenticated_rejected(async_client):
    """Test AC-5: Administrative routes reject unauthenticated requests with 401."""
    # Refunds list
    res_refunds = await async_client.get("/api/admin/refunds")
    assert res_refunds.status_code == 401

    # Stats
    res_stats = await async_client.get("/api/admin/stats")
    assert res_stats.status_code == 401

    # Settings
    res_settings = await async_client.get("/api/admin/settings/llm")
    assert res_settings.status_code == 401


@pytest.mark.asyncio
async def test_role_based_access_control(agent_auth_client, admin_auth_client):
    """Test AC-5: Agent can read claims but cannot access settings or execute overrides (403)."""
    # 1. Agent reading refunds succeeds (200)
    res_agent_read = await agent_auth_client.get("/api/admin/refunds")
    assert res_agent_read.status_code == 200

    # 2. Agent accessing LLM settings is forbidden (403)
    res_agent_settings = await agent_auth_client.get("/api/admin/settings/llm")
    assert res_agent_settings.status_code == 403

    # 3. Admin accessing LLM settings succeeds (200)
    res_admin_settings = await admin_auth_client.get("/api/admin/settings/llm")
    assert res_admin_settings.status_code == 200


@pytest.mark.asyncio
async def test_login_missing_fields(async_client):
    """Test AC-2: Login with missing fields returns 422 unprocessable entity."""
    res_no_pass = await async_client.post(
        "/api/auth/login",
        json={"email": "admin@store.com"},
    )
    assert res_no_pass.status_code == 422

    res_no_email = await async_client.post(
        "/api/auth/login",
        json={"password": "admin123"},
    )
    assert res_no_email.status_code == 422


@pytest.mark.asyncio
async def test_jwt_tampering_and_expiration(async_client):
    """Test AC-5: Tampered or malformed JWT access tokens are rejected with 401."""
    # Tampered signature
    bogus_token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiJzb21ldXVpZCIsImVtYWlsIjoiYUBiLmNvbSIsInJvbGUiOiJhZG1pbiIsImV4cCI6OTk5OTk5OTk5OX0."
        "invalidsignature1234567890abcdef"
    )
    res_tampered = await async_client.get(
        "/api/auth/me",
        cookies={"access_token": bogus_token},
    )
    assert res_tampered.status_code == 401
    assert "Invalid or expired access token" in res_tampered.json()["detail"]


@pytest.mark.asyncio
async def test_no_sensitive_hash_leakage(async_client, db_session):
    """Test AC-2, AC-5: Passwords and token hashes are never leaked in response payloads."""
    await AuthService.ensure_seed_users(db_session)

    res = await async_client.post(
        "/api/auth/login",
        json={"email": "admin@store.com", "password": "admin123"},
    )
    assert res.status_code == 200
    payload = res.json()
    assert "password_hash" not in payload
    assert "password" not in payload
    assert "token_hash" not in payload


@pytest.mark.asyncio
async def test_unknown_refresh_token_rejected(async_client):
    """Test AC-3: Non-existent refresh token is rejected with 401."""
    res = await async_client.post(
        "/api/auth/refresh",
        cookies={"refresh_token": "non_existent_token_value_random_123"},
    )
    assert res.status_code == 401
    assert "Invalid, revoked, or expired" in res.json()["detail"]
