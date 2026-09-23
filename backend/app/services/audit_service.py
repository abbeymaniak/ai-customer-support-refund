"""Audit service handling immutable logging of refund decisions and overrides."""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        action: str,
        actor: str = "system",
        refund_request_id: uuid.UUID | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        """Create and persist an immutable audit log entry."""
        audit_entry = AuditLog(
            id=uuid.uuid4(),
            refund_request_id=refund_request_id,
            action=action,
            actor=actor,
            details=details or {},
            timestamp=datetime.utcnow(),
        )
        self.db.add(audit_entry)
        await self.db.commit()
        await self.db.refresh(audit_entry)
        return audit_entry
