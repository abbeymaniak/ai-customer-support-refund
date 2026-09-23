import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.refund_request import RefundRequest


class Customer(Base):
    """Customer profile and history model."""

    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    total_spent: Mapped[float] = mapped_column(Float, default=0.0)
    orders_count: Mapped[int] = mapped_column(Integer, default=0)
    refunds_count: Mapped[int] = mapped_column(Integer, default=0)
    return_rate: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    account_created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    orders: Mapped[list["Order"]] = relationship(
        "Order", back_populates="customer", cascade="all, delete-orphan"
    )
    refund_requests: Mapped[list["RefundRequest"]] = relationship(
        "RefundRequest", back_populates="customer"
    )
