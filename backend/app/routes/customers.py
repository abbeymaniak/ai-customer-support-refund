"""Customer lookup, customer orders, and refund history API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.customer import CustomerResponse, OrderResponse
from app.schemas.refund import RefundRequestResponse
from app.services.customer_service import CustomerService

router = APIRouter()


@router.get(
    "/lookup",
    response_model=CustomerResponse,
    status_code=status.HTTP_200_OK,
    summary="Lookup customer profile by email",
    description="Retrieve customer profile metrics including total spend, return rate, and risk score.",
)
async def lookup_customer_by_email(
    email: str = Query(..., description="Customer email address to lookup"),
    db: AsyncSession = Depends(get_db),
) -> CustomerResponse:
    customer_service = CustomerService(db)
    customer = await customer_service.get_customer_by_email(email.strip().lower())
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with email '{email}' not found.",
        )
    return CustomerResponse.model_validate(customer)


@router.get(
    "/{customer_id}/orders",
    response_model=list[OrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Get customer orders",
    description="Retrieve all purchase orders and line items associated with a customer.",
)
async def get_customer_orders(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[OrderResponse]:
    customer_service = CustomerService(db)
    customer = await customer_service.get_customer(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found.",
        )
    orders = await customer_service.get_customer_orders(customer_id)
    return [OrderResponse.model_validate(order) for order in orders]


@router.get(
    "/{customer_id}/refunds",
    response_model=list[RefundRequestResponse],
    status_code=status.HTTP_200_OK,
    summary="Get customer refund history",
    description="Retrieve all refund requests for a customer, ordered by most recent first.",
)
async def get_customer_refunds(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[RefundRequestResponse]:
    customer_service = CustomerService(db)
    customer = await customer_service.get_customer(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found.",
        )
    refunds = await customer_service.get_customer_refunds(customer_id)
    return [RefundRequestResponse.model_validate(r) for r in refunds]

