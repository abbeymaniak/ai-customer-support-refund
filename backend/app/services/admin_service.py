"""Administrative service handling refund table queries, metrics aggregation, and human overrides."""

import uuid
from datetime import datetime

import structlog
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.order import Order
from app.models.refund_request import RefundRequest
from app.schemas.admin import (
    AuditLogResponse,
    RefundAdminDetailResponse,
    RefundAdminListItem,
    RefundAdminListResponse,
    RefundOverridePayload,
    RefundStatsResponse,
)
from app.services.audit_service import AuditService

logger = structlog.get_logger()


class AdminService:
    """Service layer for administrative refund operations, reporting, and triage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_refunds(
        self,
        decision: str | None = None,
        search: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 20,
        offset: int = 0,
        min_risk_score: float | None = None,
    ) -> RefundAdminListResponse:
        """Query paginated refund requests with server side filtering, search, and sorting."""
        bounded_limit = max(1, min(limit, 100))
        bounded_offset = max(0, offset)

        filters = []

        if decision and decision.lower().strip() not in ("all", ""):
            filters.append(func.lower(RefundRequest.decision) == decision.lower().strip())

        if search and search.strip():
            term = f"%{search.strip()}%"
            filters.append(
                RefundRequest.request_number.ilike(term)
                | Customer.email.ilike(term)
                | Customer.name.ilike(term)
                | Order.order_number.ilike(term)
            )

        if start_date:
            filters.append(RefundRequest.created_at >= start_date)

        if end_date:
            filters.append(RefundRequest.created_at <= end_date)

        if min_risk_score is not None:
            filters.append(RefundRequest.risk_score >= min_risk_score)

        # Count total matches
        count_stmt = (
            select(func.count(RefundRequest.id))
            .outerjoin(Customer, RefundRequest.customer_id == Customer.id)
            .outerjoin(Order, RefundRequest.order_id == Order.id)
        )
        if filters:
            count_stmt = count_stmt.where(*filters)

        total_count = (await self.db.execute(count_stmt)).scalar_one()

        # Build query for rows
        stmt = (
            select(
                RefundRequest,
                Customer.name.label("customer_name"),
                Customer.email.label("customer_email"),
                Order.order_number.label("order_number"),
            )
            .outerjoin(Customer, RefundRequest.customer_id == Customer.id)
            .outerjoin(Order, RefundRequest.order_id == Order.id)
        )
        if filters:
            stmt = stmt.where(*filters)

        # Determine sort column
        sort_column_map = {
            "created_at": RefundRequest.created_at,
            "amount": RefundRequest.amount,
            "request_number": RefundRequest.request_number,
            "decision": RefundRequest.decision,
            "status": RefundRequest.status,
            "risk_score": RefundRequest.risk_score,
        }
        order_col = sort_column_map.get(sort_by.lower(), RefundRequest.created_at)
        if sort_order.lower() == "asc":
            stmt = stmt.order_by(order_col.asc())
        else:
            stmt = stmt.order_by(order_col.desc())

        stmt = stmt.limit(bounded_limit).offset(bounded_offset)

        result = await self.db.execute(stmt)
        rows = result.all()

        items = []
        for row in rows:
            req = row[0]
            cust_name = row[1]
            cust_email = row[2]
            ord_num = row[3]
            items.append(
                RefundAdminListItem(
                    id=req.id,
                    request_number=req.request_number,
                    customer_id=req.customer_id,
                    customer_name=cust_name,
                    customer_email=cust_email,
                    order_id=req.order_id,
                    order_number=ord_num,
                    item_name=req.item_name,
                    amount=req.amount,
                    currency=req.currency,
                    reason_category=req.reason_category,
                    status=req.status,
                    decision=req.decision,
                    confidence_score=req.confidence_score,
                    human_override=req.human_override,
                    risk_score=req.risk_score,
                    anomaly_flags=req.anomaly_flags or [],
                    created_at=req.created_at,
                    updated_at=req.updated_at,
                )
            )

        return RefundAdminListResponse(
            items=items,
            total=total_count,
            limit=bounded_limit,
            offset=bounded_offset,
        )

    async def get_stats(self) -> RefundStatsResponse:
        """Compute aggregated operations metrics for administrative overview cards."""
        stmt = select(
            func.count(RefundRequest.id).label("total"),
            func.count(case((func.lower(RefundRequest.decision) == "approved", 1))).label("approved"),
            func.count(case((func.lower(RefundRequest.decision) == "denied", 1))).label("denied"),
            func.count(case((func.lower(RefundRequest.decision) == "escalated", 1))).label("escalated"),
            func.count(case((RefundRequest.human_override.is_(True), 1))).label("overrides"),
            func.coalesce(
                func.sum(
                    case((func.lower(RefundRequest.decision) == "approved", RefundRequest.amount))
                ),
                0.0,
            ).label("refunded_amount"),
        )
        row = (await self.db.execute(stmt)).one()

        total = row.total or 0
        approved = row.approved or 0
        denied = row.denied or 0
        escalated = row.escalated or 0
        overrides = row.overrides or 0
        refunded_amount = float(row.refunded_amount or 0.0)

        approval_rate = round((approved / total) * 100.0, 1) if total > 0 else 0.0

        return RefundStatsResponse(
            total_requests=total,
            approved_count=approved,
            denied_count=denied,
            escalated_count=escalated,
            approval_rate=approval_rate,
            human_overrides_count=overrides,
            total_refunded_amount=round(refunded_amount, 2),
        )

    async def get_refund_detail(self, refund_id: uuid.UUID) -> RefundAdminDetailResponse | None:
        """Retrieve full claim inspection detail including customer profile, order items, and audit trail."""
        stmt = (
            select(RefundRequest)
            .where(RefundRequest.id == refund_id)
            .options(
                selectinload(RefundRequest.customer),
                selectinload(RefundRequest.order).selectinload(Order.order_items),
                selectinload(RefundRequest.refund_items),
                selectinload(RefundRequest.audit_logs),
            )
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None

        # Sort audit logs chronologically
        sorted_logs = sorted(record.audit_logs, key=lambda log_entry: log_entry.timestamp)

        response = RefundAdminDetailResponse.model_validate(record)
        response.audit_logs = [AuditLogResponse.model_validate(log) for log in sorted_logs]
        return response

    async def override_decision(
        self,
        refund_id: uuid.UUID,
        payload: RefundOverridePayload,
    ) -> RefundAdminDetailResponse | None:
        """Apply human supervisor override, update status, and record immutable audit entry."""
        stmt = select(RefundRequest).where(RefundRequest.id == refund_id)
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None

        previous_decision = record.decision
        previous_status = record.status

        # Update record
        record.decision = payload.decision
        record.status = payload.decision.lower()
        record.human_override = True
        record.override_reason = payload.reason
        record.override_by = payload.actor
        record.updated_at = datetime.utcnow()

        await self.db.commit()

        # Create immutable audit log entry
        audit_service = AuditService(self.db)
        await audit_service.log_event(
            action="human_override",
            actor=payload.actor,
            refund_request_id=record.id,
            details={
                "previous_decision": previous_decision,
                "previous_status": previous_status,
                "new_decision": payload.decision,
                "override_reason": payload.reason,
                "override_by": payload.actor,
            },
        )

        return await self.get_refund_detail(refund_id)

    async def get_audit_logs(
        self,
        refund_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[AuditLogResponse]:
        """Fetch audit log records, optionally filtered by refund request."""
        stmt = select(AuditLog)
        if refund_id:
            stmt = stmt.where(AuditLog.refund_request_id == refund_id)
        stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(max(1, min(limit, 100)))

        result = await self.db.execute(stmt)
        records = result.scalars().all()
        return [AuditLogResponse.model_validate(r) for r in records]
