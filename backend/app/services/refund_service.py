"""Refund service handling refund lifecycle, validation, and AI integration."""

from sqlalchemy.ext.asyncio import AsyncSession


class RefundService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Full implementation in Slice 1 (core refund request loop)
