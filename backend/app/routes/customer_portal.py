"""Customer portal endpoints for authenticated order retrieval and scoped refund claims."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.customer_auth import get_current_customer
from app.models.customer import Customer
from app.schemas.customer_portal import (
    CustomerPortalOrderResponse,
    CustomerPortalRefundHistoryItemResponse,
    CustomerRefundClaimPayload,
)
from app.schemas.refund import RefundRequestResponse
from app.services.customer_portal_service import CustomerPortalService

router = APIRouter()


@router.get(
    "/orders",
    response_model=list[CustomerPortalOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Get authenticated customer orders with claim indicators",
    description="Retrieve all purchase orders and line items owned by the authenticated customer session.",
)
async def get_authenticated_customer_orders(
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
) -> list[CustomerPortalOrderResponse]:
    """Return orders belonging strictly to the authenticated customer."""
    return await CustomerPortalService.get_customer_orders_with_claims(db, current_customer.id)


@router.get(
    "/refunds",
    response_model=list[CustomerPortalRefundHistoryItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get authenticated customer refund claims history",
    description="Retrieve all refund claims filed by the authenticated customer session.",
)
async def get_authenticated_customer_refunds(
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
) -> list[CustomerPortalRefundHistoryItemResponse]:
    """Return refund claims belonging strictly to the authenticated customer."""
    return await CustomerPortalService.get_customer_refund_history(db, current_customer.id)


@router.post(
    "/refunds",
    response_model=RefundRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a refund claim from customer portal",
    description="Submit a refund claim for an order owned by the authenticated customer with automated evaluation.",
)
async def submit_authenticated_customer_refund(
    payload: CustomerRefundClaimPayload,
    request: Request,
    current_customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
) -> RefundRequestResponse:
    """Submit refund claim binding caller identity strictly to current_customer."""
    client_ip = request.client.host if request.client else None
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()

    return await CustomerPortalService.submit_customer_refund(
        db=db,
        customer=current_customer,
        payload=payload,
        client_ip=client_ip,
    )
