"""Pydantic schemas for customer and order endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CustomerResponse(BaseModel):
    """Customer profile summary including order metrics and risk score."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    total_spent: float = 0.0
    orders_count: int = 0
    refunds_count: int = 0
    return_rate: float = 0.0
    risk_score: float = 0.0
    account_created_at: datetime
    created_at: datetime
    updated_at: datetime


class OrderItemResponse(BaseModel):
    """Order line item schema with pricing and policy flags."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    order_id: uuid.UUID
    product_id: str
    name: str = Field(validation_alias="product_name")
    product_name: str
    category: str
    price: float
    quantity: int = 1
    is_final_sale: bool = False
    serial_number: str | None = None
    warranty_status: str | None = None


class OrderResponse(BaseModel):
    """Order summary with nested line items."""

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
    items: list[OrderItemResponse] = Field(default_factory=list, validation_alias="order_items")
