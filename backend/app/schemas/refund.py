"""Pydantic schemas for refund submission, evaluation, and responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RefundSubmissionPayload(BaseModel):
    """Payload submitted by customer to request a refund."""

    customer_email: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        max_length=255,
        description="Valid customer email address",
    )
    order_number: str = Field(
        ...,
        pattern=r"^ORD-[0-9A-Za-z-]{3,32}$",
        max_length=50,
        description="Order identifier prefixed with ORD-",
    )
    item_id: uuid.UUID
    amount: float = Field(..., ge=0.0, description="Requested refund amount in USD")
    reason_category: str = Field(
        ..., description="Category: damaged_on_arrival, defective, unwanted, etc."
    )
    customer_explanation: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Customer explanation notes between 10 and 1000 characters",
    )
    quantity: int = Field(default=1, ge=1, description="Quantity of units to refund")
    item_condition: str = Field(
        default="unopened", description="Condition: unopened, opened_used, damaged"
    )

    @field_validator("customer_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not cleaned or "@" not in cleaned:
            raise ValueError("Please provide a valid email address.")
        return cleaned

    @field_validator("order_number")
    @classmethod
    def validate_order_number(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned.startswith("ORD-"):
            raise ValueError("Order number must begin with 'ORD-'.")
        return cleaned

    @field_validator("customer_explanation")
    @classmethod
    def validate_explanation(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 10:
            raise ValueError("Customer explanation must contain at least 10 characters.")
        if len(cleaned) > 1000:
            raise ValueError("Customer explanation must not exceed 1000 characters.")
        return cleaned


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
    risk_score: float = 0.0
    anomaly_flags: list[str] = Field(default_factory=list)
    error_context: dict | None = None
    created_at: datetime
    updated_at: datetime
    refund_items: list[RefundItemDetail] = Field(default_factory=list)
