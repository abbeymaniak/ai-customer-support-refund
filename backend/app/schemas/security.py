"""Pydantic schemas for security incident logs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SecurityLogResponse(BaseModel):
    """Schema representing an auditable security incident."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    severity: str
    source_ip: str | None = None
    endpoint: str
    matched_pattern: str | None = None
    payload_preview: str | None = None
    customer_email: str | None = None
    order_number: str | None = None
    created_at: datetime


class SecurityLogsListResponse(BaseModel):
    """Paginated list of security incident records."""

    total: int
    items: list[SecurityLogResponse]
    limit: int
    offset: int
