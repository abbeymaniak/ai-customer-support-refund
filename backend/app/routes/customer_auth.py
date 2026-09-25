from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.customer_auth import (
    clear_customer_auth_cookies,
    get_current_customer,
    set_customer_auth_cookies,
)
from app.models.customer import Customer
from app.schemas.customer_auth import (
    CustomerAuthStatusResponse,
    CustomerLoginRequest,
    CustomerUserResponse,
)
from app.services.customer_auth_service import CustomerAuthService

router = APIRouter()


@router.post(
    "/login",
    response_model=CustomerUserResponse,
    summary="Authenticate customer and issue HTTP-only session cookies",
)
async def login(
    payload: CustomerLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> CustomerUserResponse:
    """Validate customer credentials and set customer_access_token and customer_refresh_token cookies."""
    customer = await CustomerAuthService.authenticate_customer(db, payload.email, payload.password)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = CustomerAuthService.create_access_token(customer)
    refresh_token = await CustomerAuthService.create_refresh_token(db, customer.id)

    set_customer_auth_cookies(response, access_token, refresh_token)
    return CustomerUserResponse.model_validate(customer)


@router.post(
    "/refresh",
    response_model=CustomerAuthStatusResponse,
    summary="Rotate customer refresh token and refresh access token cookie",
)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> CustomerAuthStatusResponse:
    """Rotate the single-use customer refresh token and renew short-lived access token."""
    raw_token = request.cookies.get("customer_refresh_token")
    if not raw_token:
        # Check Authorization header as fallback
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            raw_token = auth_header.split(" ", 1)[1].strip()

    if not raw_token:
        clear_customer_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer refresh token required",
        )

    result = await CustomerAuthService.rotate_refresh_token(db, raw_token)
    if not result:
        clear_customer_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, revoked, or expired customer refresh token",
        )

    customer, new_access_token, new_refresh_token = result
    set_customer_auth_cookies(response, new_access_token, new_refresh_token)

    return CustomerAuthStatusResponse(
        status="refreshed",
        message="Customer session successfully renewed",
    )


@router.post(
    "/logout",
    response_model=CustomerAuthStatusResponse,
    summary="Revoke customer refresh token and clear customer session cookies",
)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> CustomerAuthStatusResponse:
    """Revoke customer session in the database and clear all customer authentication cookies."""
    raw_token = request.cookies.get("customer_refresh_token")
    if raw_token:
        await CustomerAuthService.revoke_refresh_token(db, raw_token)

    clear_customer_auth_cookies(response)
    return CustomerAuthStatusResponse(
        status="logged_out",
        message="Successfully logged out of customer session",
    )


@router.get(
    "/me",
    response_model=CustomerUserResponse,
    summary="Retrieve current authenticated customer profile",
)
async def get_me(
    current_customer: Customer = Depends(get_current_customer),
) -> CustomerUserResponse:
    """Return profile and purchasing metrics for the active customer session."""
    return CustomerUserResponse.model_validate(current_customer)
