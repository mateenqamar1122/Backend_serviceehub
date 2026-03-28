"""
Review schemas for request/response validation.
"""
from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    """Base review schema."""
    title: str = Field(..., min_length=5, max_length=200)
    comment: str = Field(..., min_length=10, max_length=5000)
    rating: int = Field(..., ge=1, le=5)
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    professionalism_rating: Optional[int] = Field(None, ge=1, le=5)
    communication_rating: Optional[int] = Field(None, ge=1, le=5)
    punctuality_rating: Optional[int] = Field(None, ge=1, le=5)


class ReviewCreate(ReviewBase):
    """Review creation schema."""
    booking_id: UUID
    service_id: UUID


class ReviewResponse(ReviewBase):
    """Review response schema."""
    id: UUID
    booking_id: UUID
    service_id: UUID
    reviewer_id: UUID
    reviewee_id: UUID
    status: str
    is_verified_purchase: bool
    helpful_count: int = 0
    unhelpful_count: int = 0
    response: Optional[str] = None
    response_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """Review list response with pagination."""
    total: int
    page: int
    page_size: int
    average_rating: float
    rating_distribution: dict
    items: list[ReviewResponse]


class ReviewDetailResponse(ReviewResponse):
    """Detailed review response."""
    pass


class ProviderResponseSchema(BaseModel):
    """Provider response to review."""
    response: str = Field(..., min_length=10, max_length=2000)


class RatingStatsResponse(BaseModel):
    """Provider rating statistics."""
    average_rating: float
    total_reviews: int
    rating_distribution: dict
    aspect_ratings: dict

