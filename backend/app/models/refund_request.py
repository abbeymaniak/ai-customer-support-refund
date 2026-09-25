import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.customer import Customer
    from app.models.order import Order
    from app.models.refund_item import RefundItem


class RefundRequest(Base):
    """Refund request model capturing request items, AI evaluation, and resolution."""

    __tablename__ = "refund_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_number: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, default=lambda: f"REF-{uuid.uuid4().hex[:10].upper()}"
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    item_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    item_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    total_refund_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    reason_category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    customer_explanation: Mapped[str] = mapped_column(Text, nullable=False)

    # Lifecycle status: pending, approved, denied, escalated, manual_review, completed
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True, nullable=False)

    # Decision details: 'pending', 'approved', 'denied', 'escalated'
    decision: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    policy_checks: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    llm_audit_data: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    # AI decision fields
    ai_decision: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_evaluations: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)
    llm_metadata: Mapped[dict | None] = mapped_column(JSONB, default=dict, nullable=True)

    # Human override
    human_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Security and anomaly tracking fields
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, index=True)
    anomaly_flags: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    error_context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    customer: Mapped["Customer"] = relationship("Customer", back_populates="refund_requests")
    order: Mapped["Order"] = relationship("Order", back_populates="refund_requests")
    refund_items: Mapped[list["RefundItem"]] = relationship(
        "RefundItem", back_populates="refund_request", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="refund_request")
