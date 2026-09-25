import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.auth import AdminUser
from app.services.auth_service import AuthService


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set HTTP-only access and refresh token cookies."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
        secure=settings.auth_cookie_secure,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
        secure=settings.auth_cookie_secure,
        max_age=settings.refresh_token_expire_days * 86400,
        path="/api/auth",
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear HTTP-only access and refresh token cookies."""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/api/auth")


async def get_current_admin_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """FastAPI dependency to extract and validate the current admin user from cookie or Authorization header."""
    token = request.cookies.get("access_token")

    # Optional fallback to Authorization header for programmatic testing
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    payload = AuthService.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )

    try:
        user_uuid = uuid.UUID(payload.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        ) from None

    stmt = select(AdminUser).where(AdminUser.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found",
        )

    return user


def require_role(allowed_roles: list[str]) -> Callable:
    """Factory dependency to enforce role based access control."""

    async def role_checker(
        current_user: AdminUser = Depends(get_current_admin_user),
    ) -> AdminUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the following roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


require_admin = require_role(["admin"])
