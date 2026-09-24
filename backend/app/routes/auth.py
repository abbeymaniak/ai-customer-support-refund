from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import (
    clear_auth_cookies,
    get_current_admin_user,
    set_auth_cookies,
)
from app.models.auth import AdminUser
from app.schemas.auth import AdminUserResponse, AuthStatusResponse, LoginRequest
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/login",
    response_model=AdminUserResponse,
    summary="Authenticate administrative user and set HTTP-only session cookies",
)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AdminUserResponse:
    """Validate administrator credentials and issue access and refresh cookies."""
    user = await AuthService.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = AuthService.create_access_token(user)
    refresh_token = await AuthService.create_refresh_token(db, user.id)

    set_auth_cookies(response, access_token, refresh_token)
    return AdminUserResponse.model_validate(user)


@router.post(
    "/refresh",
    response_model=AuthStatusResponse,
    summary="Rotate refresh token and refresh access token cookie",
)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthStatusResponse:
    """Rotate the single-use refresh token and renew the short-lived access token."""
    raw_token = request.cookies.get("refresh_token")
    if not raw_token:
        # Check Authorization header as fallback
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            raw_token = auth_header.split(" ", 1)[1].strip()

    if not raw_token:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    result = await AuthService.rotate_refresh_token(db, raw_token)
    if not result:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, revoked, or expired refresh token",
        )

    user, new_access_token, new_refresh_token = result
    set_auth_cookies(response, new_access_token, new_refresh_token)

    return AuthStatusResponse(
        status="refreshed",
        message="Session successfully renewed",
    )


@router.post(
    "/logout",
    response_model=AuthStatusResponse,
    summary="Revoke active refresh token and clear session cookies",
)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> AuthStatusResponse:
    """Revoke session in the database and clear all authentication cookies."""
    raw_token = request.cookies.get("refresh_token")
    if raw_token:
        await AuthService.revoke_refresh_token(db, raw_token)

    clear_auth_cookies(response)
    return AuthStatusResponse(
        status="logged_out",
        message="Successfully logged out",
    )


@router.get(
    "/me",
    response_model=AdminUserResponse,
    summary="Retrieve current authenticated administrator profile",
)
async def get_me(
    current_user: AdminUser = Depends(get_current_admin_user),
) -> AdminUserResponse:
    """Return profile and role information for the active session."""
    return AdminUserResponse.model_validate(current_user)
