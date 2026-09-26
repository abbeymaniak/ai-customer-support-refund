"""Pydantic schemas for the authenticated customer refund portal."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CustomerPortalOrderItemResponse(BaseModel):
    """Order line item schema with refund claim state indicators."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    order_id: uuid.UUID
    product_id: str
    product_name: str
    name: str = Field(validation_alias="product_name")
    category: str
    price: float
    quantity: int = 1
    is_final_sale: bool = False
    serial_number: str | None = None
    warranty_status: str | None = None
    has_active_claim: bool = False
    claim_status: str | None = None
    claim_request_number: str | None = None


class CustomerPortalOrderResponse(BaseModel):
    """Customer order summary with enriched item claim indicators."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    order_number: str
    order_date: datetime
    delivery_date: datetime | None = None
    delivered_date: datetime | None = Field(default=None, validation_alias="delivery_date")
    total_amount: float
    currency: str = "USD"
    status: str
    items: list[CustomerPortalOrderItemResponse] = Field(
        default_factory=list, validation_alias="order_items"
    )


class CustomerPortalRefundClaimItemResponse(BaseModel):
    """Line item details attached to a customer refund claim."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    order_item_id: uuid.UUID
    product_name: str
    quantity: int = 1
    refund_amount: float
    item_condition: str = "unopened"


class CustomerPortalRefundHistoryItemResponse(BaseModel):
    """Enriched customer refund claim history schema for portal inspection."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    request_number: str
    order_id: uuid.UUID
    order_number: str
    item_name: str | None = None
    amount: float
    currency: str = "USD"
    status: str
    decision: str
    ai_decision: str | None = None
    confidence_score: float | None = None
    reason_category: str
    customer_explanation: str
    ai_reasoning: str | None = None
    policy_checks: dict | list | None = None
    human_override: bool = False
    override_reason: str | None = None
    override_by: str | None = None
    items: list[CustomerPortalRefundClaimItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime | None = None


class CustomerRefundClaimPayload(BaseModel):
    """Payload for submitting a refund claim from an authenticated customer portal session."""

    order_id: uuid.UUID = Field(..., description="Target order identifier owned by customer")
    item_id: uuid.UUID = Field(..., description="Target order line item to be refunded")
    reason_category: str = Field(
        ...,
        description="Reason category (e.g. damaged_on_arrival, defective, unwanted, wrong_item, not_as_described, late_delivery)",
    )
    customer_explanation: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Customer explanation notes between 10 and 1000 characters",
    )
    quantity: int = Field(default=1, ge=1, description="Quantity of units to refund")
    item_condition: str = Field(
        default="unopened",
        description="Condition of the item: unopened, opened_used, damaged",
    )

    @field_validator("customer_explanation")
    @classmethod
    def validate_explanation(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 10:
            raise ValueError("Explanation must be at least 10 characters long.")
        if len(cleaned) > 1000:
            raise ValueError("Explanation cannot exceed 1000 characters.")
        return cleaned

    @field_validator("reason_category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        cleaned = v.strip().lower()
        valid_categories = {
            "damaged_on_arrival",
            "defective",
            "unwanted",
            "wrong_item",
            "not_as_described",
            "late_delivery",
            "other",
        }
        if cleaned not in valid_categories:
            raise ValueError(f"Invalid reason category. Must be one of: {', '.join(sorted(valid_categories))}")
        return cleaned

    @field_validator("item_condition")
    @classmethod
    def validate_condition(cls, v: str) -> str:
        cleaned = v.strip().lower()
        valid_conditions = {"unopened", "opened_used", "damaged"}
        if cleaned not in valid_conditions:
            raise ValueError(f"Invalid item condition. Must be one of: {', '.join(sorted(valid_conditions))}")
        return cleaned
