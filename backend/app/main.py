from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import setup_logging
from app.database import async_session
from app.db.seed import seed_database
from app.routes import (
    admin,
    admin_security,
    admin_settings,
    auth,
    customer_auth,
    customer_portal,
    customers,
    health,
    refunds,
)

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan ensuring default test credentials and seed profiles exist."""
    async with async_session() as session:
        try:
            await seed_database(session)
        except Exception:
            pass
    yield


app = FastAPI(
    title="AI Customer Support Refund System",
    description="AI-powered refund request processing with policy enforcement and audit logging",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(customer_auth.router, prefix="/api/customer/auth", tags=["Customer Authentication"])
app.include_router(customer_portal.router, prefix="/api/customer", tags=["Customer Portal"])
app.include_router(refunds.router, prefix="/api/refunds", tags=["Refunds"])
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(admin_security.router, prefix="/api/admin", tags=["Admin Security"])
app.include_router(admin_settings.router, prefix="/api/admin/settings", tags=["Admin Settings"])
