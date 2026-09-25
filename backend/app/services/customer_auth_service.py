import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.auth import RefreshToken
from app.models.customer import Customer
from app.schemas.customer_auth import CustomerTokenPayload


class CustomerAuthService:
    """Handles customer authentication, token lifecycle, and cryptographic rotation."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plain text password using bcrypt with work factor 12."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a bcrypt hash."""
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

    @staticmethod
    def hash_token(raw_token: str) -> str:
        """Generate SHA-256 hash of a raw token string for secure database persistence."""
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def create_access_token(customer: Customer) -> str:
        """Generate a short lived JWT access token for a customer."""
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)
        payload = {
            "sub": str(customer.id),
            "email": customer.email,
            "name": customer.name,
            "role": "customer",
            "jti": secrets.token_hex(8),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_access_token(token: str) -> CustomerTokenPayload | None:
        """Decode and validate a customer JWT access token."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            if payload.get("role") != "customer":
                return None

            return CustomerTokenPayload(
                sub=payload["sub"],
                email=payload["email"],
                name=payload["name"],
                role=payload["role"],
                exp=payload["exp"],
            )
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError):
            return None

    @classmethod
    async def authenticate_customer(
        cls, session: AsyncSession, email: str, password: str
    ) -> Customer | None:
        """Authenticate customer by email and password, updating last_login_at upon success."""
        normalized_email = email.strip().lower()
        stmt = select(Customer).where(Customer.email == normalized_email)
        result = await session.execute(stmt)
        customer = result.scalar_one_or_none()

        if not customer or not customer.is_active:
            return None

        if not cls.verify_password(password, customer.password_hash):
            return None

        customer.last_login_at = datetime.utcnow()
        await session.commit()
        await session.refresh(customer)
        return customer

    @classmethod
    async def create_refresh_token(cls, session: AsyncSession, customer_id: uuid.UUID) -> str:
        """Create and persist a cryptographic refresh token for a customer."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = cls.hash_token(raw_token)
        expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

        token_record = RefreshToken(
            id=uuid.uuid4(),
            user_id=None,
            customer_id=customer_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False,
            created_at=datetime.utcnow(),
        )
        session.add(token_record)
        await session.commit()
        return raw_token

    @classmethod
    async def rotate_refresh_token(
        cls, session: AsyncSession, raw_token: str
    ) -> tuple[Customer, str, str] | None:
        """Rotate a customer refresh token: revoke existing, issue fresh pair, return customer and tokens."""
        if not raw_token:
            return None

        token_hash = cls.hash_token(raw_token)
        stmt = (
            select(RefreshToken)
            .options(selectinload(RefreshToken.customer))
            .where(RefreshToken.token_hash == token_hash)
        )
        result = await session.execute(stmt)
        token_record = result.scalar_one_or_none()

        if not token_record or token_record.customer_id is None:
            return None

        # Replay or expiration detection
        if token_record.revoked or token_record.expires_at < datetime.utcnow():
            return None

        customer = token_record.customer
        if not customer or not customer.is_active:
            return None

        # Revoke old token
        token_record.revoked = True

        # Generate new refresh token
        new_raw_token = secrets.token_urlsafe(32)
        new_token_hash = cls.hash_token(new_raw_token)
        new_expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

        new_record = RefreshToken(
            id=uuid.uuid4(),
            user_id=None,
            customer_id=customer.id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            revoked=False,
            created_at=datetime.utcnow(),
        )
        session.add(new_record)

        # Generate new access token
        new_access_token = cls.create_access_token(customer)

        await session.commit()
        await session.refresh(customer)
        return customer, new_access_token, new_raw_token

    @classmethod
    async def revoke_refresh_token(cls, session: AsyncSession, raw_token: str) -> bool:
        """Revoke a customer refresh token on logout."""
        if not raw_token:
            return True

        token_hash = cls.hash_token(raw_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await session.execute(stmt)
        token_record = result.scalar_one_or_none()

        if token_record and token_record.customer_id is not None:
            token_record.revoked = True
            await session.commit()
        return True
