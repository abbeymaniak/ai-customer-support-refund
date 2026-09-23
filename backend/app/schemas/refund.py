"""Pydantic schemas for refund submission, evaluation, and responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RefundSubmissionPayload(BaseModel):
    """Payload submitted by customer to request a refund."""

    customer_email: str
    order_number: str
    item_id: uuid.UUID
    amount: float = Field(..., ge=0.0, description="Requested refund amount in USD")
    reason_category: str = Field(
        ..., description="Category: damaged_on_arrival, defective, unwanted, etc."
    )
    customer_explanation: str = Field(..., min_length=3, description="Customer explanation notes")
    quantity: int = Field(default=1, ge=1, description="Quantity of units to refund")
    item_condition: str = Field(
        default="unopened", description="Condition: unopened, opened_used, damaged"
    )


class RefundItemDetail(BaseModel):
    """Line item in a refund request."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_item_id: uuid.UUID
    quantity: int
    refund_amount: float
    item_condition: str


class RefundRequestResponse(BaseModel):
    """Complete detail of an evaluated refund request."""

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
    human_override: bool = False
    override_reason: str | None = None
    override_by: str | None = None
    created_at: datetime
    updated_at: datetime
    refund_items: list[RefundItemDetail] = Field(default_factory=list)
