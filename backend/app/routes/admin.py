"""Administrative API route handlers for refund claims, KPI statistics, and overrides."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.admin import (
    AuditLogResponse,
    RefundAdminDetailResponse,
    RefundAdminListResponse,
    RefundOverridePayload,
    RefundStatsResponse,
)
from app.services.admin_service import AdminService

router = APIRouter()


@router.get(
    "/refunds",
    response_model=RefundAdminListResponse,
    status_code=status.HTTP_200_OK,
    summary="List refund requests with filters",
    description="Retrieve paginated list of claims with optional status, search, and date filters.",
)
async def list_refund_requests(
    decision: str | None = Query(default=None, description="Status filter: Approved, Denied, Escalated, or all"),
    search: str | None = Query(default=None, description="Search by customer email, name, order, or request number"),
    start_date: datetime | None = Query(default=None, description="Start date boundary (ISO 8601)"),
    end_date: datetime | None = Query(default=None, description="End date boundary (ISO 8601)"),
    sort_by: str = Query(default="created_at", description="Sort column: created_at, amount, request_number, decision"),
    sort_order: str = Query(default="desc", description="Sort direction: asc or desc"),
    limit: int = Query(default=20, ge=1, le=100, description="Page record limit"),
    offset: int = Query(default=0, ge=0, description="Page record offset"),
    db: AsyncSession = Depends(get_db),
) -> RefundAdminListResponse:
    admin_service = AdminService(db)
    return await admin_service.list_refunds(
        decision=decision,
        search=search,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/stats",
    response_model=RefundStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get refund operational metrics",
    description="Calculate aggregate volume, approval percentage, overrides, and total refunded amount.",
)
async def get_refund_stats(
    db: AsyncSession = Depends(get_db),
) -> RefundStatsResponse:
    admin_service = AdminService(db)
    return await admin_service.get_stats()


@router.get(
    "/refunds/{id}",
    response_model=RefundAdminDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed claim review",
    description="Retrieve comprehensive claim record with customer metrics, order items, and audit logs.",
)
async def get_refund_detail(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RefundAdminDetailResponse:
    admin_service = AdminService(db)
    detail = await admin_service.get_refund_detail(id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Refund claim with id '{id}' not found.",
        )
    return detail


@router.post(
    "/refunds/{id}/override",
    response_model=RefundAdminDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Override automated decision",
    description="Manually approve, deny, or escalate a claim with a mandatory supervisor rationale.",
)
async def override_refund_decision(
    id: uuid.UUID,
    payload: RefundOverridePayload,
    db: AsyncSession = Depends(get_db),
) -> RefundAdminDetailResponse:
    admin_service = AdminService(db)
    updated = await admin_service.override_decision(id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Refund claim with id '{id}' not found.",
        )
    return updated


@router.get(
    "/audit-logs",
    response_model=list[AuditLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Query audit log entries",
    description="List system and human audit logs, optionally filtered by refund claim.",
)
async def list_audit_logs(
    refund_id: uuid.UUID | None = Query(default=None, description="Optional refund claim UUID"),
    limit: int = Query(default=50, ge=1, le=100, description="Log record limit"),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogResponse]:
    admin_service = AdminService(db)
    return await admin_service.get_audit_logs(refund_id=refund_id, limit=limit)
