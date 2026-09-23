from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import setup_logging
from app.routes import admin, admin_settings, customers, health, refunds

setup_logging()

app = FastAPI(
    title="AI Customer Support Refund System",
    description="AI-powered refund request processing with policy enforcement and audit logging",
    version="1.0.0",
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
app.include_router(refunds.router, prefix="/api/refunds", tags=["Refunds"])
app.include_router(customers.router, prefix="/api/customers", tags=["Customers"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(
    admin_settings.router, prefix="/api/admin/settings", tags=["Admin Settings"]
)
