"""SecurityLog model for tracking prompt injection attempts, input validation failures, and suspicious activities."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SecurityLog(Base):
    """Audit record for prompt injection, XSS attempts, or security policy violations."""

    __tablename__ = "security_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), default="high", nullable=False, index=True)
    source_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    matched_pattern: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload_preview: Mapped[str | None] = mapped_column(String(500), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    order_number: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True, nullable=False
    )
