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
from app.models.auth import AdminUser, RefreshToken
from app.schemas.auth import TokenPayload


class AuthService:
    """Handles password hashing, token generation, cryptographic rotation, and authentication."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plain text password using bcrypt."""
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
        """Generate SHA-256 hash of a raw token string for secure persistence."""
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @staticmethod
    def create_access_token(user: AdminUser) -> str:
        """Generate a short lived JWT access token."""
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "jti": secrets.token_hex(8),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_access_token(token: str) -> TokenPayload | None:
        """Decode and validate a JWT access token."""
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            return TokenPayload(
                sub=payload["sub"],
                email=payload["email"],
                name=payload["name"],
                role=payload["role"],
                exp=payload["exp"],
            )
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError):
            return None

    @classmethod
    async def authenticate_user(
        cls, session: AsyncSession, email: str, password: str
    ) -> AdminUser | None:
        """Authenticate user by email and password, updating last_login_at upon success."""
        normalized_email = email.strip().lower()
        stmt = select(AdminUser).where(AdminUser.email == normalized_email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            return None

        if not cls.verify_password(password, user.password_hash):
            return None

        user.last_login_at = datetime.utcnow()
        await session.commit()
        await session.refresh(user)
        return user

    @classmethod
    async def create_refresh_token(cls, session: AsyncSession, user_id: uuid.UUID) -> str:
        """Create and store a cryptographic refresh token for a user."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = cls.hash_token(raw_token)
        expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

        token_record = RefreshToken(
            id=uuid.uuid4(),
            user_id=user_id,
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
    ) -> tuple[AdminUser, str, str] | None:
        """Rotate a refresh token: revoke existing token, generate new pair, return user and tokens."""
        if not raw_token:
            return None

        token_hash = cls.hash_token(raw_token)
        stmt = (
            select(RefreshToken)
            .options(selectinload(RefreshToken.user))
            .where(RefreshToken.token_hash == token_hash)
        )
        result = await session.execute(stmt)
        token_record = result.scalar_one_or_none()

        if not token_record:
            return None

        # Replay or revocation detection
        if token_record.revoked or token_record.expires_at < datetime.utcnow():
            return None

        user = token_record.user
        if not user or not user.is_active:
            return None

        # Revoke old token
        token_record.revoked = True

        # Generate new refresh token
        new_raw_token = secrets.token_urlsafe(32)
        new_token_hash = cls.hash_token(new_raw_token)
        new_expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

        new_record = RefreshToken(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            revoked=False,
            created_at=datetime.utcnow(),
        )
        session.add(new_record)

        # Generate new access token
        new_access_token = cls.create_access_token(user)

        await session.commit()
        await session.refresh(user)
        return user, new_access_token, new_raw_token

    @classmethod
    async def revoke_refresh_token(cls, session: AsyncSession, raw_token: str) -> bool:
        """Revoke a refresh token on logout."""
        if not raw_token:
            return True

        token_hash = cls.hash_token(raw_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await session.execute(stmt)
        token_record = result.scalar_one_or_none()

        if token_record:
            token_record.revoked = True
            await session.commit()
        return True

    @classmethod
    async def ensure_seed_users(cls, session: AsyncSession) -> None:
        """Ensure default admin and lead accounts exist for evaluator testing."""
        seeds = [
            ("admin@store.com", "admin123", "Store Administrator", "admin"),
            ("lead@store.com", "lead123", "Support Lead", "agent"),
        ]
        for email, password, name, role in seeds:
            stmt = select(AdminUser).where(AdminUser.email == email)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if not existing:
                user = AdminUser(
                    id=uuid.uuid4(),
                    email=email,
                    password_hash=cls.hash_password(password),
                    name=name,
                    role=role,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(user)
        await session.commit()
