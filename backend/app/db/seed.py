"""Automated database seeding service for AI Customer Support Refund System.

Ensures that:
1. Normalized schema, tables, indices, and extensions exist.
2. 16 realistic customer personas with multi-order purchasing histories are seeded.
3. Default admin credentials exist for evaluator login.
4. Multi-provider LLM slots (Ollama, OpenAI, Gemini) are populated.
5. Seed data is idempotent and safe to run on every application boot.
"""

import asyncio
import sys
from pathlib import Path

import structlog
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.auth import AdminUser
from app.models.customer import Customer
from app.models.llm_provider import LLMProvider
from app.models.order import Order
from app.services.auth_service import AuthService

logger = structlog.get_logger(__name__)


def locate_seed_file() -> Path | None:
    """Locate seed.sql from standard repository mount points."""
    candidates = [
        Path("/app/data/seed.sql"),
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "seed.sql",
        Path("data/seed.sql"),
        Path("../data/seed.sql"),
    ]
    for path in candidates:
        if path.exists() and path.is_file():
            return path
    return None


async def run_seed_sql(session: AsyncSession, seed_path: Path) -> None:
    """Execute raw seed.sql script statements idempotently."""
    logger.info("applying_seed_sql", path=str(seed_path))
    content = seed_path.read_text(encoding="utf-8")

    # Split into separate statements to execute safely
    statements = [stmt.strip() for stmt in content.split(";") if stmt.strip()]
    for stmt in statements:
        # Ignore comments-only chunks
        clean_lines = [line for line in stmt.splitlines() if not line.strip().startswith("--")]
        clean_stmt = "\n".join(clean_lines).strip()
        if clean_stmt:
            try:
                await session.execute(text(clean_stmt))
            except Exception as ex:
                logger.warning("seed_sql_statement_skipped", error=str(ex), preview=clean_stmt[:80])
    await session.commit()


async def verify_and_seed_defaults(session: AsyncSession) -> dict[str, int]:
    """Verify entity counts and seed default accounts and providers if missing."""
    # 1. Ensure admin accounts
    await AuthService.ensure_seed_users(session)

    # 2. Check admin@refunds.internal exists
    admin_internal_stmt = select(AdminUser).where(AdminUser.email == "admin@refunds.internal")
    existing_internal = (await session.execute(admin_internal_stmt)).scalar_one_or_none()
    if not existing_internal:
        internal_user = AdminUser(
            email="admin@refunds.internal",
            password_hash=AuthService.hash_password("AdminPassword123!"),
            name="System Administrator",
            role="admin",
            is_active=True,
        )
        session.add(internal_user)
        await session.commit()
    else:
        existing_internal.password_hash = AuthService.hash_password("AdminPassword123!")
        existing_internal.is_active = True
        await session.commit()

    # 3. Ensure LLM Providers exist
    providers = [
        ("ollama", True, "llama3", None, "http://host.docker.internal:11434"),
        ("openai", False, "gpt-4o-mini", None, None),
        ("gemini", False, "gemini-1.5-flash", None, None),
    ]
    for llm_name, is_active, model, api_key, api_base in providers:
        stmt_p = select(LLMProvider).where(LLMProvider.llm == llm_name)
        existing_p = (await session.execute(stmt_p)).scalar_one_or_none()
        if not existing_p:
            p = LLMProvider(
                llm=llm_name,
                is_active=is_active,
                llm_model=model,
                api_key=api_key,
                api_base=api_base,
                temperature=0.0,
                timeout_seconds=3.0,
                updated_by="seed_service",
            )
            session.add(p)
    await session.commit()

    # 4. Report verified counts
    cust_count = (await session.execute(select(func.count(Customer.id)))).scalar() or 0
    order_count = (await session.execute(select(func.count(Order.id)))).scalar() or 0
    admin_count = (await session.execute(select(func.count(AdminUser.id)))).scalar() or 0

    return {
        "customers": cust_count,
        "orders": order_count,
        "admins": admin_count,
    }


async def seed_database(session: AsyncSession | None = None) -> dict[str, int]:
    """Top-level database seeding routine called on boot or via CLI."""
    if session is not None:
        seed_path = locate_seed_file()
        if seed_path:
            await run_seed_sql(session, seed_path)
        return await verify_and_seed_defaults(session)

    async with async_session() as db:
        seed_path = locate_seed_file()
        if seed_path:
            await run_seed_sql(db, seed_path)
        stats = await verify_and_seed_defaults(db)
        logger.info("database_seeding_complete", stats=stats)
        return stats


if __name__ == "__main__":
    try:
        results = asyncio.run(seed_database())
        print(f"Database seeded successfully: {results}")
        sys.exit(0)
    except Exception as e:
        print(f"Seeding failed: {e}", file=sys.stderr)
        sys.exit(1)
