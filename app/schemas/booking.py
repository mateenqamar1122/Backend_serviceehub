"""
Booking schemas for request/response validation.
"""
from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BookingBase(BaseModel):
    """Base booking schema."""
    service_id: UUID
    scheduled_date: datetime
    duration_hours: int = Field(..., gt=0, le=24)
    notes: Optional[str] = None


class BookingCreate(BookingBase):
    """Booking creation schema."""
    pass


class BookingUpdate(BaseModel):
    """Booking update schema."""
    status: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    duration_hours: Optional[int] = None
    notes: Optional[str] = None


class BookingReview(BaseModel):
    """Booking review schema."""
    rating: float = Field(..., ge=1, le=5)
    review: str = Field(..., min_length=10)


class BookingResponse(BookingBase):
    """Booking response schema."""
    id: UUID
    customer_id: UUID
    provider_id: UUID
    status: str
    total_price: float
    rating: Optional[float] = None
    review: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingDetailResponse(BookingResponse):
    """Detailed booking response schema."""
    pass


class BookingListResponse(BaseModel):
    """Booking list response with pagination."""
    total: int
    page: int
    page_size: int
    items: list[BookingResponse]

