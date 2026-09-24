"""Pydantic schemas for administrative refund management and statistics."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.customer import CustomerResponse, OrderResponse
from app.schemas.refund import RefundItemDetail


class RefundAdminListItem(BaseModel):
    """Summary item for administrative table listing."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    request_number: str
    customer_id: uuid.UUID
    customer_name: str | None = None
    customer_email: str | None = None
    order_id: uuid.UUID
    order_number: str | None = None
    item_name: str | None = None
    amount: float
    currency: str = "USD"
    reason_category: str
    status: str
    decision: str
    confidence_score: float | None = None
    human_override: bool = False
    created_at: datetime
    updated_at: datetime


class RefundAdminListResponse(BaseModel):
    """Paginated envelope for administrative refund queries."""

    items: list[RefundAdminListItem]
    total: int
    limit: int
    offset: int


class RefundStatsResponse(BaseModel):
    """Executive KPI metrics for refund operations."""

    total_requests: int
    approved_count: int
    denied_count: int
    escalated_count: int
    approval_rate: float
    human_overrides_count: int
    total_refunded_amount: float


class AuditLogResponse(BaseModel):
    """Audit log entry for claim history timeline."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    refund_request_id: uuid.UUID | None = None
    action: str
    actor: str
    details: dict = Field(default_factory=dict)
    timestamp: datetime


class RefundAdminDetailResponse(BaseModel):
    """Detailed claim inspection schema with nested relationships."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    request_number: str
    customer_id: uuid.UUID
    order_id: uuid.UUID
    item_id: str | None = None
    item_name: str | None = None
    amount: float
    total_refund_amount: float
    currency: str = "USD"
    reason_category: str
    customer_explanation: str
    status: str
    decision: str
    decision_reason: str | None = None
    confidence_score: float | None = None
    policy_checks: dict | None = None
    llm_audit_data: dict | None = None
    ai_decision: str | None = None
    ai_confidence: float | None = None
    ai_reasoning: str | None = None
    policy_evaluations: dict | None = None
    llm_metadata: dict | None = None
    human_override: bool = False
    override_reason: str | None = None
    override_by: str | None = None
    created_at: datetime
    updated_at: datetime
    customer: CustomerResponse | None = None
    order: OrderResponse | None = None
    refund_items: list[RefundItemDetail] = Field(default_factory=list)
    audit_logs: list[AuditLogResponse] = Field(default_factory=list)


class RefundOverridePayload(BaseModel):
    """Payload to apply manual manager decision override."""

    decision: Literal["Approved", "Denied", "Escalated"]
    reason: str = Field(..., min_length=5, description="Mandatory justification explanation")
    actor: str = Field(default="support_lead@store.com", description="Supervisor identifier")

    @field_validator("reason")
    @classmethod
    def validate_reason_non_empty(cls, value: str) -> str:
        trimmed = value.strip()
        if len(trimmed) < 5:
            raise ValueError("Override reason must contain at least 5 non whitespace characters")
        return trimmed
