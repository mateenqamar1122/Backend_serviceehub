"""
Subscription schemas for request/response validation.
"""
from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SubscriptionPlanSchema(BaseModel):
    """Subscription plan details."""
    name: str
    price_per_month: float
    max_active_services: int
    featured_listings_count: int
    priority_support: bool
    analytics_dashboard: bool


class SubscriptionCreate(BaseModel):
    """Subscription creation schema."""
    plan: str = Field(..., regex="^(basic|pro|premium)$")
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None


class SubscriptionUpgrade(BaseModel):
    """Plan upgrade schema."""
    new_plan: str = Field(..., regex="^(basic|pro|premium)$")
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None


class SubscriptionCancel(BaseModel):
    """Subscription cancellation schema."""
    reason: Optional[str] = Field(None, max_length=500)


class SubscriptionResponse(BaseModel):
    """Subscription response schema."""
    id: UUID
    provider_id: UUID
    plan: str
    status: str
    price_per_month: float
    currency: str
    start_date: datetime
    end_date: datetime
    renewal_date: datetime
    auto_renew: bool
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    max_active_services: int
    featured_listings_count: int
    featured_listings_used: int
    priority_support: bool
    analytics_dashboard: bool
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeaturedListingRequest(BaseModel):
    """Featured listing request schema."""
    service_id: UUID


class SubscriptionStatsResponse(BaseModel):
    """Subscription statistics response."""
    current_plan: str
    status: str
    max_active_services: int
    featured_listings_available: int
    featured_listings_used: int
    priority_support: bool
    analytics_dashboard: bool
    days_until_renewal: int
    auto_renew: bool


class PlanComparisonResponse(BaseModel):
    """Plan comparison details."""
    plans: dict

