"""Customer service handling customer lookup, order history, and fraud signals."""

from sqlalchemy.ext.asyncio import AsyncSession


class CustomerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Full implementation in Slice 1
