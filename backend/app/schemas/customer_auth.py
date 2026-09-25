import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CustomerLoginRequest(BaseModel):
    """Payload for customer authentication."""

    email: str = Field(..., min_length=3, description="Customer email address")
    password: str = Field(..., min_length=1, description="Account password")


class CustomerUserResponse(BaseModel):
    """Public profile for an authenticated customer."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    role: str = "customer"
    is_active: bool
    total_spent: float = 0.0
    orders_count: int = 0
    refunds_count: int = 0
    return_rate: float = 0.0
    risk_score: float = 0.0
    last_login_at: datetime | None = None
    created_at: datetime


class CustomerTokenPayload(BaseModel):
    """Decoded customer JWT access token claims."""

    sub: str  # Customer UUID string
    email: str
    name: str
    role: str = "customer"
    exp: int


class CustomerAuthStatusResponse(BaseModel):
    """Status acknowledgment for customer refresh and logout operations."""

    status: Literal["ok", "refreshed", "logged_out"]
    message: str | None = None
