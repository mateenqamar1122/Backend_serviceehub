"""
API routes package initialization.
"""
from fastapi import APIRouter

from app.api.routes import (
    auth, users, services, bookings, health, auth_examples,
    providers, websocket, reviews, subscriptions
)

api_router = APIRouter()

# Include route modules
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(auth_examples.router)
api_router.include_router(users.router)
api_router.include_router(services.router)
api_router.include_router(bookings.router)
api_router.include_router(providers.router)
api_router.include_router(websocket.router)
api_router.include_router(reviews.router)
api_router.include_router(subscriptions.router)

__all__ = ["api_router"]

