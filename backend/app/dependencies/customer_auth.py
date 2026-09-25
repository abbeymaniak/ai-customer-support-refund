import uuid

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.customer import Customer
from app.services.customer_auth_service import CustomerAuthService


def set_customer_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set HTTP-only customer access and refresh token cookies."""
    response.set_cookie(
        key="customer_access_token",
        value=access_token,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
        secure=settings.auth_cookie_secure,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key="customer_refresh_token",
        value=refresh_token,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
        secure=settings.auth_cookie_secure,
        max_age=settings.refresh_token_expire_days * 86400,
        path="/api/customer/auth",
    )


def clear_customer_auth_cookies(response: Response) -> None:
    """Clear HTTP-only customer access and refresh token cookies."""
    response.delete_cookie(key="customer_access_token", path="/")
    response.delete_cookie(key="customer_refresh_token", path="/api/customer/auth")


async def get_current_customer(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Customer:
    """FastAPI dependency to extract and validate the active customer from cookie or Authorization header."""
    token = request.cookies.get("customer_access_token")

    # Optional fallback to Authorization header for programmatic testing
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer authentication required",
        )

    payload = CustomerAuthService.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired customer access token",
        )

    try:
        customer_uuid = uuid.UUID(payload.sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        ) from None

    stmt = select(Customer).where(Customer.id == customer_uuid)
    result = await db.execute(stmt)
    customer = result.scalar_one_or_none()

    if not customer or not customer.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer account is inactive or not found",
        )

    return customer
