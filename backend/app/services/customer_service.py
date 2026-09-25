"""Customer service handling customer lookup, order history, and fraud metric calculations."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.order import Order
from app.models.refund_request import RefundRequest


class CustomerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_customer(self, customer_id: uuid.UUID) -> Customer | None:
        """Fetch customer profile by UUID."""
        stmt = select(Customer).where(Customer.id == customer_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_customer_by_email(self, email: str) -> Customer | None:
        """Fetch customer profile by email."""
        stmt = select(Customer).where(Customer.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def recalculate_customer_metrics(self, customer_id: uuid.UUID) -> Customer | None:
        """Recalculate and update cached risk and financial metrics for a customer."""
        customer = await self.get_customer(customer_id)
        if not customer:
            return None

        # Calculate total spend and order count
        order_stats_stmt = select(
            func.coalesce(func.sum(Order.total_amount), 0.0).label("total_spent"),
            func.count(Order.id).label("orders_count"),
        ).where(Order.customer_id == customer_id)
        order_stats = (await self.db.execute(order_stats_stmt)).one()

        # Calculate approved refund count
        refund_count_stmt = select(func.count(RefundRequest.id)).where(
            RefundRequest.customer_id == customer_id,
            RefundRequest.status.in_(["approved", "completed"]),
        )
        refunds_count = (await self.db.execute(refund_count_stmt)).scalar() or 0

        total_spent = float(order_stats.total_spent)
        orders_count = int(order_stats.orders_count)
        return_rate = float(refunds_count / orders_count) if orders_count > 0 else 0.0

        # Heuristic risk score calculation: weighted return rate and frequency
        base_risk = min(1.0, return_rate * 1.5)
        if refunds_count > 3:
            base_risk = min(1.0, base_risk + 0.2)
        if orders_count > 10 and return_rate < 0.1:
            base_risk = max(0.02, base_risk - 0.1)

        customer.total_spent = round(total_spent, 2)
        customer.orders_count = orders_count
        customer.refunds_count = refunds_count
        customer.return_rate = round(return_rate, 4)
        customer.risk_score = round(base_risk, 4)
        customer.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(customer)
        return customer

    async def get_customer_orders(self, customer_id: uuid.UUID) -> list[Order]:
        """Fetch all orders for a customer with loaded order items."""
        stmt = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .options(selectinload(Order.order_items))
            .order_by(Order.order_date.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_customer_refunds(self, customer_id: uuid.UUID) -> list[RefundRequest]:
        """Fetch all refund requests for a customer, most recent first."""
        stmt = (
            select(RefundRequest)
            .where(RefundRequest.customer_id == customer_id)
            .options(selectinload(RefundRequest.refund_items))
            .order_by(RefundRequest.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

