"""Service layer for customer portal operations, order retrieval, and scoped claims."""

import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.refund_item import RefundItem
from app.models.refund_request import RefundRequest
from app.schemas.customer_portal import (
    CustomerPortalOrderItemResponse,
    CustomerPortalOrderResponse,
    CustomerRefundClaimPayload,
)
from app.schemas.refund import RefundRequestResponse, RefundSubmissionPayload
from app.services.refund_service import RefundService

logger = structlog.get_logger()


class CustomerPortalService:
    """Handles scoped customer order listing with claim states and validated refund claims."""

    @staticmethod
    async def get_customer_orders_with_claims(
        db: AsyncSession,
        customer_id: uuid.UUID,
    ) -> list[CustomerPortalOrderResponse]:
        """Fetch all orders for a customer with item claim status badges."""
        stmt = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(Order.order_date.desc())
            .options(
                selectinload(Order.order_items)
                .selectinload(OrderItem.refund_items)
                .selectinload(RefundItem.refund_request)
            )
        )
        result = await db.execute(stmt)
        orders = result.scalars().all()

        portal_orders: list[CustomerPortalOrderResponse] = []
        for order in orders:
            portal_items: list[CustomerPortalOrderItemResponse] = []
            for item in order.order_items:
                has_active = False
                claim_status_val: str | None = None
                claim_req_num: str | None = None

                # Inspect refund items attached to this order item
                for rf_item in item.refund_items:
                    rf_req = rf_item.refund_request
                    if rf_req:
                        has_active = True
                        claim_status_val = rf_req.decision if rf_req.decision else rf_req.status
                        claim_req_num = rf_req.request_number
                        break

                portal_items.append(
                    CustomerPortalOrderItemResponse(
                        id=item.id,
                        order_id=item.order_id,
                        product_id=item.product_id,
                        product_name=item.product_name,
                        name=item.product_name,
                        category=item.category,
                        price=item.price,
                        quantity=item.quantity,
                        is_final_sale=item.is_final_sale,
                        serial_number=item.serial_number,
                        warranty_status=item.warranty_status,
                        has_active_claim=has_active,
                        claim_status=claim_status_val,
                        claim_request_number=claim_req_num,
                    )
                )

            portal_orders.append(
                CustomerPortalOrderResponse(
                    id=order.id,
                    customer_id=order.customer_id,
                    order_number=order.order_number,
                    order_date=order.order_date,
                    delivery_date=order.delivery_date,
                    delivered_date=order.delivery_date,
                    total_amount=order.total_amount,
                    currency=order.currency,
                    status=order.status,
                    items=portal_items,
                )
            )

        return portal_orders

    @staticmethod
    async def submit_customer_refund(
        db: AsyncSession,
        customer: Customer,
        payload: CustomerRefundClaimPayload,
        client_ip: str | None = None,
    ) -> RefundRequestResponse:
        """Validate order ownership and submit customer refund claim through evaluation pipeline."""
        # 1. Fetch order with items
        stmt = (
            select(Order)
            .where(Order.id == payload.order_id)
            .options(selectinload(Order.order_items))
        )
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found.",
            )

        # 2. Strict order customer ownership enforcement
        if order.customer_id != customer.id:
            logger.warning(
                "customer_order_ownership_mismatch",
                customer_id=str(customer.id),
                order_id=str(order.id),
                order_customer_id=str(order.customer_id),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Order does not belong to the authenticated customer.",
            )

        # 3. Locate line item in order
        target_item = next((i for i in order.order_items if i.id == payload.item_id), None)
        if not target_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specified item does not belong to this order.",
            )

        # 4. Check requested quantity bounds
        if payload.quantity > target_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Requested quantity ({payload.quantity}) exceeds purchased quantity ({target_item.quantity}).",
            )

        # 5. Check if an active or approved claim already exists for this order item
        claim_check_stmt = (
            select(RefundItem)
            .join(RefundRequest, RefundItem.refund_request_id == RefundRequest.id)
            .where(
                RefundItem.order_item_id == target_item.id,
            )
        )
        existing_claim_result = await db.execute(claim_check_stmt)
        if existing_claim_result.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A refund claim has already been filed for this item.",
            )

        # 6. Derive amount automatically from unit price and quantity
        derived_amount = round(float(target_item.price * payload.quantity), 2)

        # 7. Construct standard RefundSubmissionPayload binding authenticated customer identity
        submission_payload = RefundSubmissionPayload(
            customer_email=customer.email,
            order_number=order.order_number,
            item_id=target_item.id,
            amount=derived_amount,
            reason_category=payload.reason_category,
            customer_explanation=payload.customer_explanation,
            quantity=payload.quantity,
            item_condition=payload.item_condition,
        )

        # 8. Delegate to RefundService for full evaluation and persistence
        refund_service = RefundService(db)
        refund_record = await refund_service.process_refund(submission_payload, client_ip=client_ip)

        return RefundRequestResponse.model_validate(refund_record)
