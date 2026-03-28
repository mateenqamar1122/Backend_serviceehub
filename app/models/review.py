"""
Review model for Supabase.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.db.base import BaseModel


class ReviewStatus:
    """Review status constants."""
    PENDING = "pending"
    PUBLISHED = "published"
    FLAGGED = "flagged"


class Review(BaseModel):
    """Review model for service ratings."""

    def __init__(
        self,
        id: Optional[UUID] = None,
        booking_id: Optional[UUID] = None,
        service_id: Optional[UUID] = None,
        reviewer_id: Optional[UUID] = None,
        reviewee_id: Optional[UUID] = None,
        rating: int = 5,
        title: Optional[str] = None,
        comment: Optional[str] = None,
        quality_rating: Optional[int] = None,
        professionalism_rating: Optional[int] = None,
        communication_rating: Optional[int] = None,
        punctuality_rating: Optional[int] = None,
        status: str = ReviewStatus.PUBLISHED,
        is_verified_purchase: bool = True,
        helpful_count: int = 0,
        unhelpful_count: int = 0,
        response: Optional[str] = None,
        response_date: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        **kwargs,
    ):
        """Initialize Review model."""
        super().__init__(**kwargs)
        self.id = id
        self.booking_id = booking_id
        self.service_id = service_id
        self.reviewer_id = reviewer_id
        self.reviewee_id = reviewee_id
        self.rating = rating
        self.title = title
        self.comment = comment
        self.quality_rating = quality_rating
        self.professionalism_rating = professionalism_rating
        self.communication_rating = communication_rating
        self.punctuality_rating = punctuality_rating
        self.status = status
        self.is_verified_purchase = is_verified_purchase
        self.helpful_count = helpful_count
        self.unhelpful_count = unhelpful_count
        self.response = response
        self.response_date = response_date
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, booking_id={self.booking_id}, rating={self.rating})>"

