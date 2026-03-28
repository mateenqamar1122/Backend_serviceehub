"""
Service model for ServiceHub marketplace.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

from app.db.base import BaseModel


class ServiceCategory(str, Enum):
    """Service categories."""
    CLEANING = "cleaning"
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    CARPENTRY = "carpentry"
    PAINTING = "painting"
    LANDSCAPING = "landscaping"
    TUTORING = "tutoring"
    OTHER = "other"


class Service(BaseModel):
    """Service model for marketplace services."""

    def __init__(
        self,
        id: Optional[UUID] = None,
        provider_id: Optional[UUID] = None,
        title: str = "",
        description: str = "",
        category: str = "",
        price_per_hour: float = 0.0,
        rating: Optional[float] = None,
        number_of_reviews: Optional[int] = None,
        is_available: bool = True,
        location: Optional[str] = None,
        tags: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        **kwargs,
    ):
        """Initialize Service model."""
        super().__init__(**kwargs)
        self.id = id
        self.provider_id = provider_id
        self.title = title
        self.description = description
        self.category = category
        self.price_per_hour = price_per_hour
        self.rating = rating
        self.number_of_reviews = number_of_reviews
        self.is_available = is_available
        self.location = location
        self.tags = tags
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self) -> str:
        return f"<Service(id={self.id}, title={self.title}, provider_id={self.provider_id})>"

