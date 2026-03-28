"""
Main FastAPI application entry point using Supabase.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.api import api_router
from app.api.middleware import (
    AuthenticationMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware,
    RateLimitMiddleware,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info(f"✅ ServiceHub API started - Version {settings.app_version}")
    logger.info(f"📡 Connected to Supabase: {settings.supabase_url}")
    logger.info(f"🔐 Authentication enabled with Supabase Auth")
    logger.info(f"🌍 Environment: {settings.environment}")
    yield
    # Shutdown
    logger.info("❌ ServiceHub API shutting down...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        description="A production-ready service marketplace backend API with Supabase Auth",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Add middleware stack (order matters - added in reverse order of execution)

    # Rate limiting middleware
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=600,  # 10 requests per second
    )

    # Error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)

    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Authentication middleware (checks protected routes)
    app.add_middleware(AuthenticationMiddleware)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.example.com"],
    )

    # Include API routes
    app.include_router(
        api_router,
        prefix=settings.api_prefix,
    )

    logger.info("✅ FastAPI application configured with authentication middleware")
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info",
    )

