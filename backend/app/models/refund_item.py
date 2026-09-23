import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.order_item import OrderItem
    from app.models.refund_request import RefundRequest


class RefundItem(Base):
    """Line item within a refund request tying back to a purchased order item."""

    __tablename__ = "refund_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    refund_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("refund_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("order_items.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    refund_amount: Mapped[float] = mapped_column(Float, nullable=False)
    item_condition: Mapped[str] = mapped_column(String(64), default="unopened", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    refund_request: Mapped["RefundRequest"] = relationship(
        "RefundRequest", back_populates="refund_items"
    )
    order_item: Mapped["OrderItem"] = relationship("OrderItem", back_populates="refund_items")
