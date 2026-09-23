import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.customer import Customer
    from app.models.order import Order


class RefundRequest(Base):
    """Refund request model capturing request, AI decision, and resolution."""

    __tablename__ = "refund_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )
    item_id: Mapped[str] = mapped_column(String(64), nullable=True)
    item_name: Mapped[str] = mapped_column(String(255), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    reason_category: Mapped[str] = mapped_column(String(64), nullable=False)
    customer_explanation: Mapped[str] = mapped_column(Text, nullable=False)

    # Decision details: 'pending', 'approved', 'denied', 'escalated'
    decision: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    decision_reason: Mapped[str] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    policy_checks: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=True)
    llm_audit_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=True)

    # Human override
    human_override: Mapped[bool] = mapped_column(default=False)
    override_reason: Mapped[str] = mapped_column(Text, nullable=True)
    override_by: Mapped[str] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="refund_requests")
    order: Mapped["Order"] = relationship("Order", back_populates="refund_requests")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="refund_request")
