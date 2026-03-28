"""
Health check endpoint.
"""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "ServiceHub API"}


@router.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Welcome to ServiceHub API",
        "version": "1.0.0",
        "docs": "/docs",
    }

