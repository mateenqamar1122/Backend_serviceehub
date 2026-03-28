"""
Subscription service business logic using Supabase.

Handles:
- Creating subscriptions for providers
- Managing subscription status
- Plan upgrades/downgrades
- Featured listing tracking
- Renewal management
"""
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime, timedelta

from supabase import Client

from app.models import Subscription, SubscriptionPlan, SubscriptionStatus


# Subscription plan configurations
PLAN_CONFIG = {
    SubscriptionPlan.BASIC: {
        "price_per_month": 9.99,
        "max_active_services": 5,
        "featured_listings_count": 0,
        "priority_support": False,
        "analytics_dashboard": False,
    },
    SubscriptionPlan.PRO: {
        "price_per_month": 29.99,
        "max_active_services": 25,
        "featured_listings_count": 3,
        "priority_support": True,
        "analytics_dashboard": False,
    },
    SubscriptionPlan.PREMIUM: {
        "price_per_month": 99.99,
        "max_active_services": 100,
        "featured_listings_count": 10,
        "priority_support": True,
        "analytics_dashboard": True,
    },
}


class SubscriptionService:
    """Service for subscription operations."""

    @staticmethod
    async def create_subscription(
        supabase: Client,
        provider_id: UUID,
        plan: str,
        payment_method: str = None,
        transaction_id: str = None,
        notes: str = None,
    ) -> Optional[Subscription]:
        """
        Create a new subscription for provider.

        Args:
            supabase: Supabase client
            provider_id: Provider user ID
            plan: Plan type (basic, pro, premium)
            payment_method: Payment method used
            transaction_id: Payment transaction ID
            notes: Optional notes

        Returns:
            Subscription object or None if failed
        """
        try:
            if plan not in PLAN_CONFIG:
                return None

            config = PLAN_CONFIG[plan]
            now = datetime.utcnow()

            subscription_data = {
                "provider_id": str(provider_id),
                "plan": plan,
                "status": SubscriptionStatus.ACTIVE,
                "price_per_month": config["price_per_month"],
                "currency": "USD",
                "start_date": now.isoformat(),
                "end_date": (now + timedelta(days=30)).isoformat(),
                "renewal_date": (now + timedelta(days=30)).isoformat(),
                "auto_renew": True,
                "max_active_services": config["max_active_services"],
                "featured_listings_count": config["featured_listings_count"],
                "featured_listings_used": 0,
                "priority_support": config["priority_support"],
                "analytics_dashboard": config["analytics_dashboard"],
            }

            if payment_method:
                subscription_data["payment_method"] = payment_method
            if transaction_id:
                subscription_data["transaction_id"] = transaction_id
            if notes:
                subscription_data["notes"] = notes

            response = supabase.table("subscriptions").insert(subscription_data).execute()

            if response.data and len(response.data) > 0:
                return Subscription(**response.data[0])

            return None
        except Exception as e:
            print(f"Error creating subscription: {str(e)}")
            return None

    @staticmethod
    async def get_provider_subscription(
        supabase: Client,
        provider_id: UUID,
    ) -> Optional[Subscription]:
        """
        Get active subscription for provider.

        Args:
            supabase: Supabase client
            provider_id: Provider user ID

        Returns:
            Subscription object or None
        """
        try:
            response = supabase.table("subscriptions").select("*").eq(
                "provider_id", str(provider_id)
            ).eq("status", SubscriptionStatus.ACTIVE).execute()

            if response.data and len(response.data) > 0:
                return Subscription(**response.data[0])

            return None
        except Exception as e:
            print(f"Error getting subscription: {str(e)}")
            return None

    @staticmethod
    async def upgrade_plan(
        supabase: Client,
        provider_id: UUID,
        new_plan: str,
        payment_method: str = None,
        transaction_id: str = None,
    ) -> Optional[Subscription]:
        """
        Upgrade provider's subscription plan.

        Args:
            supabase: Supabase client
            provider_id: Provider user ID
            new_plan: New plan type
            payment_method: Payment method
            transaction_id: Transaction ID

        Returns:
            Updated Subscription or None
        """
        try:
            if new_plan not in PLAN_CONFIG:
                return None

            # Get current subscription
            current = await SubscriptionService.get_provider_subscription(
                supabase, provider_id
            )

            if not current:
                return None

            config = PLAN_CONFIG[new_plan]
            now = datetime.utcnow()

            update_data = {
                "plan": new_plan,
                "price_per_month": config["price_per_month"],
                "max_active_services": config["max_active_services"],
                "featured_listings_count": config["featured_listings_count"],
                "priority_support": config["priority_support"],
                "analytics_dashboard": config["analytics_dashboard"],
                "featured_listings_used": 0,  # Reset on upgrade
            }

            if payment_method:
                update_data["payment_method"] = payment_method
            if transaction_id:
                update_data["transaction_id"] = transaction_id

            response = supabase.table("subscriptions").update(update_data).eq(
                "provider_id", str(provider_id)
            ).eq("status", SubscriptionStatus.ACTIVE).execute()

            if response.data and len(response.data) > 0:
                return Subscription(**response.data[0])

            return None
        except Exception as e:
            print(f"Error upgrading plan: {str(e)}")
            return None

    @staticmethod
    async def cancel_subscription(
        supabase: Client,
        provider_id: UUID,
        reason: str = None,
    ) -> Optional[Subscription]:
        """
        Cancel provider's subscription.

        Args:
            supabase: Supabase client
            provider_id: Provider user ID
            reason: Cancellation reason

        Returns:
            Cancelled Subscription or None
        """
        try:
            update_data = {
                "status": SubscriptionStatus.CANCELLED,
                "cancelled_at": datetime.utcnow().isoformat(),
            }

            if reason:
                update_data["cancellation_reason"] = reason

            response = supabase.table("subscriptions").update(update_data).eq(
                "provider_id", str(provider_id)
            ).eq("status", SubscriptionStatus.ACTIVE).execute()

            if response.data and len(response.data) > 0:
                return Subscription(**response.data[0])

            return None
        except Exception as e:
            print(f"Error cancelling subscription: {str(e)}")
            return None

    @staticmethod
    async def add_featured_listing(
        supabase: Client,
        provider_id: UUID,
        service_id: UUID,
    ) -> bool:
        """
        Mark service as featured (uses featured listing slot).

        Args:
            supabase: Supabase client
            provider_id: Provider user ID
            service_id: Service ID to feature

        Returns:
            True if successful
        """
        try:
            # Get subscription
            subscription = await SubscriptionService.get_provider_subscription(
                supabase, provider_id
            )

            if not subscription:
                return False

            # Check if has featured slots available
            available_slots = (
                subscription.featured_listings_count -
                subscription.featured_listings_used
            )

            if available_slots <= 0:
                return False

            # Get service and check owner
            service_response = supabase.table("services").select(
                "provider_id, is_featured"
            ).eq("id", str(service_id)).execute()

            if not service_response.data:
                return False

            service = service_response.data[0]

            # Verify provider owns service
            if service["provider_id"] != str(provider_id):
                return False

            # Mark service as featured
            supabase.table("services").update({
                "is_featured": True,
            }).eq("id", str(service_id)).execute()

            # Increment featured used count
            supabase.table("subscriptions").update({
                "featured_listings_used": subscription.featured_listings_used + 1,
            }).eq("provider_id", str(provider_id)).eq(
                "status", SubscriptionStatus.ACTIVE
            ).execute()

            return True
        except Exception as e:
            print(f"Error adding featured listing: {str(e)}")
            return False

    @staticmethod
    async def remove_featured_listing(
        supabase: Client,
        provider_id: UUID,
        service_id: UUID,
    ) -> bool:
        """
        Remove featured status from service.

        Args:
            supabase: Supabase client
            provider_id: Provider user ID
            service_id: Service ID to unfeature

        Returns:
            True if successful
        """
        try:
            # Verify provider owns service
            service_response = supabase.table("services").select(
                "provider_id, is_featured"
            ).eq("id", str(service_id)).execute()

            if not service_response.data:
                return False

            service = service_response.data[0]

            if service["provider_id"] != str(provider_id):
                return False

            # Remove featured status
            supabase.table("services").update({
                "is_featured": False,
            }).eq("id", str(service_id)).execute()

            # Decrement featured used count
            subscription = await SubscriptionService.get_provider_subscription(
                supabase, provider_id
            )

            if subscription and subscription.featured_listings_used > 0:
                supabase.table("subscriptions").update({
                    "featured_listings_used": subscription.featured_listings_used - 1,
                }).eq("provider_id", str(provider_id)).eq(
                    "status", SubscriptionStatus.ACTIVE
                ).execute()

            return True
        except Exception as e:
            print(f"Error removing featured listing: {str(e)}")
            return False

    @staticmethod
    async def check_featured_eligibility(
        supabase: Client,
        provider_id: UUID,
    ) -> bool:
        """
        Check if provider has available featured listing slots.

        Args:
            supabase: Supabase client
            provider_id: Provider user ID

        Returns:
            True if slots available
        """
        try:
            subscription = await SubscriptionService.get_provider_subscription(
                supabase, provider_id
            )

            if not subscription:
                return False

            available = (
                subscription.featured_listings_count -
                subscription.featured_listings_used
            )

            return available > 0
        except Exception as e:
            print(f"Error checking eligibility: {str(e)}")
            return False

    @staticmethod
    async def renew_subscription(
        supabase: Client,
        provider_id: UUID,
    ) -> Optional[Subscription]:
        """
        Renew subscription for next billing period.

        Args:
            supabase: Supabase client
            provider_id: Provider user ID

        Returns:
            Renewed Subscription or None
        """
        try:
            subscription = await SubscriptionService.get_provider_subscription(
                supabase, provider_id
            )

            if not subscription or not subscription.auto_renew:
                return None

            now = datetime.utcnow()
            new_end_date = now + timedelta(days=30)

            update_data = {
                "start_date": now.isoformat(),
                "end_date": new_end_date.isoformat(),
                "renewal_date": new_end_date.isoformat(),
                "featured_listings_used": 0,  # Reset featured usage
            }

            response = supabase.table("subscriptions").update(update_data).eq(
                "provider_id", str(provider_id)
            ).eq("status", SubscriptionStatus.ACTIVE).execute()

            if response.data and len(response.data) > 0:
                return Subscription(**response.data[0])

            return None
        except Exception as e:
            print(f"Error renewing subscription: {str(e)}")
            return None

    @staticmethod
    async def get_plan_config(plan: str) -> Optional[Dict]:
        """
        Get configuration for a plan.

        Args:
            plan: Plan type

        Returns:
            Plan config dict or None
        """
        return PLAN_CONFIG.get(plan)

    @staticmethod
    async def get_all_plans() -> Dict:
        """
        Get all available plans with details.

        Returns:
            Dict of all plans with configurations
        """
        return PLAN_CONFIG

    @staticmethod
    async def get_subscription_history(
        supabase: Client,
        provider_id: UUID,
        limit: int = 10,
    ) -> List[Subscription]:
        """
        Get subscription history for provider.

        Args:
            supabase: Supabase client
            provider_id: Provider user ID
            limit: Number of records to fetch

        Returns:
            List of subscriptions
        """
        try:
            response = supabase.table("subscriptions").select("*").eq(
                "provider_id", str(provider_id)
            ).order("created_at", desc=True).limit(limit).execute()

            return [Subscription(**s) for s in response.data or []]
        except Exception as e:
            print(f"Error getting subscription history: {str(e)}")
            return []

    @staticmethod
    async def expire_expired_subscriptions(supabase: Client) -> int:
        """
        Mark expired subscriptions as expired (cleanup job).

        Args:
            supabase: Supabase client

        Returns:
            Number of subscriptions expired
        """
        try:
            now = datetime.utcnow().isoformat()

            response = supabase.table("subscriptions").update({
                "status": SubscriptionStatus.EXPIRED,
            }).eq("status", SubscriptionStatus.ACTIVE).lt(
                "end_date", now
            ).execute()

            return len(response.data) if response.data else 0
        except Exception as e:
            print(f"Error expiring subscriptions: {str(e)}")
            return 0

