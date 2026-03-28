"""
Subscription model for provider plans.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.db.base import BaseModel


class SubscriptionPlan:
    """Subscription plan constants."""
    BASIC = "basic"
    PRO = "pro"
    PREMIUM = "premium"


class SubscriptionStatus:
    """Subscription status constants."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"


class Subscription(BaseModel):
    """Subscription model for provider plans."""

    def __init__(
        self,
        id: Optional[UUID] = None,
        provider_id: Optional[UUID] = None,
        plan: str = SubscriptionPlan.BASIC,
        status: str = SubscriptionStatus.PENDING,
        price_per_month: float = 0.0,
        currency: str = "USD",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        renewal_date: Optional[datetime] = None,
        auto_renew: bool = True,
        cancelled_at: Optional[datetime] = None,
        cancellation_reason: Optional[str] = None,
        max_active_services: int = 5,
        featured_listings_count: int = 0,
        featured_listings_used: int = 0,
        priority_support: bool = False,
        analytics_dashboard: bool = False,
        payment_method: Optional[str] = None,
        transaction_id: Optional[str] = None,
        notes: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        **kwargs,
    ):
        """Initialize Subscription model."""
        super().__init__(**kwargs)
        self.id = id
        self.provider_id = provider_id
        self.plan = plan
        self.status = status
        self.price_per_month = price_per_month
        self.currency = currency
        self.start_date = start_date
        self.end_date = end_date
        self.renewal_date = renewal_date
        self.auto_renew = auto_renew
        self.cancelled_at = cancelled_at
        self.cancellation_reason = cancellation_reason
        self.max_active_services = max_active_services
        self.featured_listings_count = featured_listings_count
        self.featured_listings_used = featured_listings_used
        self.priority_support = priority_support
        self.analytics_dashboard = analytics_dashboard
        self.payment_method = payment_method
        self.transaction_id = transaction_id
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, provider_id={self.provider_id}, plan={self.plan}, status={self.status})>"

