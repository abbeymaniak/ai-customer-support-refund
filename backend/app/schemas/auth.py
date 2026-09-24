import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Payload for admin authentication."""

    email: str = Field(..., min_length=3, description="Administrative user email address")
    password: str = Field(..., min_length=1, description="Account password")


class AdminUserResponse(BaseModel):
    """Public profile for an authenticated administrator or agent."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    role: str
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime


class TokenPayload(BaseModel):
    """Decoded JWT access token claims."""

    sub: str  # User UUID string
    email: str
    name: str
    role: str
    exp: int


class AuthStatusResponse(BaseModel):
    """Simple status acknowledgment for refresh and logout operations."""

    status: Literal["ok", "refreshed", "logged_out"]
    message: str | None = None
