import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LLMProvider(Base):
    """Configuration and state for an AI LLM provider."""

    __tablename__ = "llm_providers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    llm: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    llm_model: Mapped[str] = mapped_column(String(64), nullable=False)
    api_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    api_base: Mapped[str | None] = mapped_column(String(255), nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    timeout_seconds: Mapped[float] = mapped_column(Float, default=3.0, nullable=False)
    updated_by: Mapped[str | None] = mapped_column(
        String(128), default="system", nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
