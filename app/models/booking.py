"""
Booking/Order model for Supabase.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from enum import Enum

from app.db.base import BaseModel


class BookingStatus(str, Enum):
    """Booking status enum."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DECLINED = "declined"


class Booking(BaseModel):
    """Booking model for service orders."""

    def __init__(
        self,
        id: Optional[UUID] = None,
        service_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        provider_id: Optional[UUID] = None,
        status: str = BookingStatus.PENDING.value,
        scheduled_date: Optional[datetime] = None,
        scheduled_time: Optional[str] = None,
        duration_hours: int = 0,
        hourly_rate: float = 0.0,
        total_price: float = 0.0,
        customer_notes: Optional[str] = None,
        provider_notes: Optional[str] = None,
        location: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        postal_code: Optional[str] = None,
        cancelled_by: Optional[UUID] = None,
        cancellation_reason: Optional[str] = None,
        cancelled_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        actual_duration_hours: Optional[float] = None,
        customer_review_id: Optional[UUID] = None,
        provider_review_id: Optional[UUID] = None,
        rating: Optional[float] = None,
        review: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        **kwargs,
    ):
        """Initialize Booking model."""
        super().__init__(**kwargs)
        self.id = id
        self.service_id = service_id
        self.customer_id = customer_id
        self.provider_id = provider_id
        self.status = status
        self.scheduled_date = scheduled_date
        self.scheduled_time = scheduled_time
        self.duration_hours = duration_hours
        self.hourly_rate = hourly_rate
        self.total_price = total_price
        self.customer_notes = customer_notes
        self.provider_notes = provider_notes
        self.location = location
        self.address = address
        self.city = city
        self.postal_code = postal_code
        self.cancelled_by = cancelled_by
        self.cancellation_reason = cancellation_reason
        self.cancelled_at = cancelled_at
        self.completed_at = completed_at
        self.actual_duration_hours = actual_duration_hours
        self.customer_review_id = customer_review_id
        self.provider_review_id = provider_review_id
        self.rating = rating
        self.review = review
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self) -> str:
        return f"<Booking(id={self.id}, status={self.status}, customer_id={self.customer_id})>"

