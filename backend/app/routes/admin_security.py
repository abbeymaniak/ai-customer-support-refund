"""Admin routes for inspecting security incident logs and prompt injection attempts."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_role
from app.models.auth import AdminUser
from app.schemas.security import SecurityLogsListResponse
from app.services.security_service import SecurityService

router = APIRouter()


@router.get(
    "/security-logs",
    response_model=SecurityLogsListResponse,
    status_code=status.HTTP_200_OK,
    summary="List security incident logs",
    description="Retrieve paginated security incident logs with optional filtering by event type and severity.",
)
async def list_security_logs(
    limit: int = Query(default=50, ge=1, le=200, description="Number of log records to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    event_type: str | None = Query(
        default=None,
        description="Filter by event type, e.g. prompt_injection_attempt, xss_payload_detected",
    ),
    severity: str | None = Query(
        default=None,
        description="Filter by severity level: low, medium, high, critical",
    ),
    current_user: AdminUser = Depends(require_role(["admin", "agent"])),
    db: AsyncSession = Depends(get_db),
) -> SecurityLogsListResponse:
    """Retrieve security audit records with filters."""
    logs, total = await SecurityService.list_security_logs(
        db=db,
        event_type=event_type,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    return SecurityLogsListResponse(
        total=total,
        items=logs,
        limit=limit,
        offset=offset,
    )
