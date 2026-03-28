"""
Service schemas for request/response validation.
"""
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ServiceBase(BaseModel):
    """Base service schema."""
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    category: str
    price_per_hour: float = Field(..., gt=0)
    location: Optional[str] = None
    tags: Optional[str] = None  # JSON array as string


class ServiceCreate(ServiceBase):
    """Service creation schema."""
    pass


class ServiceUpdate(BaseModel):
    """Service update schema."""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price_per_hour: Optional[float] = None
    location: Optional[str] = None
    tags: Optional[str] = None
    is_available: Optional[bool] = None


class ServiceResponse(ServiceBase):
    """Service response schema."""
    id: UUID
    provider_id: UUID
    rating: Optional[float] = None
    number_of_reviews: Optional[int] = None
    is_available: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ServiceDetailResponse(ServiceResponse):
    """Detailed service response schema."""
    pass


class ServiceListResponse(BaseModel):
    """Service list response with pagination."""
    total: int
    page: int
    page_size: int
    items: List[ServiceResponse]

