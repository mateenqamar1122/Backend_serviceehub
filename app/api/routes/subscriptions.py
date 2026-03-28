"""
Subscription endpoints for provider monetization.

Features:
- Create/manage subscriptions
- Plan upgrades
- Featured listing management
- Subscription history
- Plan comparison
"""
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from app.api.dependencies import get_current_active_user, get_current_provider
from app.db import get_supabase
from app.models import User, SubscriptionPlan, SubscriptionStatus
from app.schemas import (
    SubscriptionCreate, SubscriptionUpgrade, SubscriptionCancel,
    SubscriptionResponse, FeaturedListingRequest, SubscriptionStatsResponse,
    PlanComparisonResponse
)
from app.services import SubscriptionService

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_provider),
    supabase: Client = Depends(get_supabase),
) -> SubscriptionResponse:
    """
    Create a subscription for provider.

    **Authorization**: Provider only

    **Request**:
    ```json
    {
      "plan": "pro",
      "payment_method": "credit_card",
      "transaction_id": "txn_123456",
      "notes": "Optional notes"
    }
    ```

    **Returns**: 201 Subscription created

    **Errors**:
    - 400: Invalid plan
    - 409: Already has active subscription

    **Plans Available**:
    - basic: $9.99/month - 5 services, no featured listings
    - pro: $29.99/month - 25 services, 3 featured listings
    - premium: $99.99/month - 100 services, 10 featured listings
    """
    try:
        # Check if already has active subscription
        existing = await SubscriptionService.get_provider_subscription(
            supabase, current_user.id
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already has active subscription",
            )

        # Validate plan
        plan_config = await SubscriptionService.get_plan_config(subscription_data.plan)
        if not plan_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan",
            )

        # Create subscription
        subscription = await SubscriptionService.create_subscription(
            supabase,
            current_user.id,
            subscription_data.plan,
            subscription_data.payment_method,
            subscription_data.transaction_id,
            subscription_data.notes,
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create subscription",
            )

        return SubscriptionResponse(
            id=subscription.id,
            provider_id=subscription.provider_id,
            plan=subscription.plan,
            status=subscription.status,
            price_per_month=subscription.price_per_month,
            currency=subscription.currency,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            renewal_date=subscription.renewal_date,
            auto_renew=subscription.auto_renew,
            cancelled_at=subscription.cancelled_at,
            cancellation_reason=subscription.cancellation_reason,
            max_active_services=subscription.max_active_services,
            featured_listings_count=subscription.featured_listings_count,
            featured_listings_used=subscription.featured_listings_used,
            priority_support=subscription.priority_support,
            analytics_dashboard=subscription.analytics_dashboard,
            payment_method=subscription.payment_method,
            transaction_id=subscription.transaction_id,
            notes=subscription.notes,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating subscription: {str(e)}",
        )


@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_provider),
    supabase: Client = Depends(get_supabase),
) -> SubscriptionResponse:
    """
    Get current active subscription for provider.

    **Authorization**: Provider only

    **Returns**: 200 Current subscription details

    **Errors**: 404 No active subscription

    **Example**:
    ```
    GET /api/v1/subscriptions/current
    ```
    """
    try:
        subscription = await SubscriptionService.get_provider_subscription(
            supabase, current_user.id
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription",
            )

        return SubscriptionResponse(
            id=subscription.id,
            provider_id=subscription.provider_id,
            plan=subscription.plan,
            status=subscription.status,
            price_per_month=subscription.price_per_month,
            currency=subscription.currency,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            renewal_date=subscription.renewal_date,
            auto_renew=subscription.auto_renew,
            cancelled_at=subscription.cancelled_at,
            cancellation_reason=subscription.cancellation_reason,
            max_active_services=subscription.max_active_services,
            featured_listings_count=subscription.featured_listings_count,
            featured_listings_used=subscription.featured_listings_used,
            priority_support=subscription.priority_support,
            analytics_dashboard=subscription.analytics_dashboard,
            payment_method=subscription.payment_method,
            transaction_id=subscription.transaction_id,
            notes=subscription.notes,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving subscription: {str(e)}",
        )


@router.post("/upgrade", response_model=SubscriptionResponse)
async def upgrade_subscription(
    upgrade_data: SubscriptionUpgrade,
    current_user: User = Depends(get_current_provider),
    supabase: Client = Depends(get_supabase),
) -> SubscriptionResponse:
    """
    Upgrade subscription plan.

    **Authorization**: Provider only

    **Request**:
    ```json
    {
      "new_plan": "premium",
      "payment_method": "credit_card",
      "transaction_id": "txn_789012"
    }
    ```

    **Returns**: 200 Upgraded subscription

    **Errors**:
    - 400: Invalid plan
    - 404: No active subscription

    **Example**:
    ```
    POST /api/v1/subscriptions/upgrade
    ```
    """
    try:
        # Validate plan
        plan_config = await SubscriptionService.get_plan_config(upgrade_data.new_plan)
        if not plan_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan",
            )

        # Upgrade plan
        subscription = await SubscriptionService.upgrade_plan(
            supabase,
            current_user.id,
            upgrade_data.new_plan,
            upgrade_data.payment_method,
            upgrade_data.transaction_id,
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription to upgrade",
            )

        return SubscriptionResponse(
            id=subscription.id,
            provider_id=subscription.provider_id,
            plan=subscription.plan,
            status=subscription.status,
            price_per_month=subscription.price_per_month,
            currency=subscription.currency,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            renewal_date=subscription.renewal_date,
            auto_renew=subscription.auto_renew,
            cancelled_at=subscription.cancelled_at,
            cancellation_reason=subscription.cancellation_reason,
            max_active_services=subscription.max_active_services,
            featured_listings_count=subscription.featured_listings_count,
            featured_listings_used=subscription.featured_listings_used,
            priority_support=subscription.priority_support,
            analytics_dashboard=subscription.analytics_dashboard,
            payment_method=subscription.payment_method,
            transaction_id=subscription.transaction_id,
            notes=subscription.notes,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error upgrading subscription: {str(e)}",
        )


@router.post("/cancel", response_model=dict)
async def cancel_subscription(
    cancel_data: SubscriptionCancel,
    current_user: User = Depends(get_current_provider),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Cancel subscription.

    **Authorization**: Provider only

    **Request**:
    ```json
    {
      "reason": "Not using the service anymore"
    }
    ```

    **Returns**: 200 Cancellation confirmed

    **Errors**: 404 No active subscription

    **Example**:
    ```
    POST /api/v1/subscriptions/cancel
    ```
    """
    try:
        subscription = await SubscriptionService.cancel_subscription(
            supabase, current_user.id, cancel_data.reason
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription to cancel",
            )

        return {
            "id": str(subscription.id),
            "status": "cancelled",
            "message": "Subscription cancelled successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling subscription: {str(e)}",
        )


@router.get("/stats", response_model=SubscriptionStatsResponse)
async def get_subscription_stats(
    current_user: User = Depends(get_current_provider),
    supabase: Client = Depends(get_supabase),
) -> SubscriptionStatsResponse:
    """
    Get subscription statistics.

    **Authorization**: Provider only

    **Returns**: 200 Subscription stats

    **Example**:
    ```
    GET /api/v1/subscriptions/stats
    ```
    """
    try:
        subscription = await SubscriptionService.get_provider_subscription(
            supabase, current_user.id
        )

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription",
            )

        # Calculate days until renewal
        renewal_date = subscription.renewal_date
        if isinstance(renewal_date, str):
            renewal_date = datetime.fromisoformat(renewal_date.replace('Z', '+00:00'))

        days_until = (renewal_date - datetime.utcnow()).days

        featured_available = (
            subscription.featured_listings_count -
            subscription.featured_listings_used
        )

        return SubscriptionStatsResponse(
            current_plan=subscription.plan,
            status=subscription.status,
            max_active_services=subscription.max_active_services,
            featured_listings_available=featured_available,
            featured_listings_used=subscription.featured_listings_used,
            priority_support=subscription.priority_support,
            analytics_dashboard=subscription.analytics_dashboard,
            days_until_renewal=max(days_until, 0),
            auto_renew=subscription.auto_renew,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting stats: {str(e)}",
        )


@router.post("/featured", response_model=dict, status_code=status.HTTP_200_OK)
async def add_featured_listing(
    listing_data: FeaturedListingRequest,
    current_user: User = Depends(get_current_provider),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Add service to featured listings.

    **Authorization**: Provider only

    **Request**:
    ```json
    {
      "service_id": "uuid"
    }
    ```

    **Returns**: 200 Service featured

    **Errors**:
    - 400: No featured slots available or invalid service
    - 404: Subscription or service not found

    **Example**:
    ```
    POST /api/v1/subscriptions/featured
    ```
    """
    try:
        # Check eligibility
        is_eligible = await SubscriptionService.check_featured_eligibility(
            supabase, current_user.id
        )

        if not is_eligible:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No featured listing slots available",
            )

        # Add featured listing
        success = await SubscriptionService.add_featured_listing(
            supabase, current_user.id, listing_data.service_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to feature service",
            )

        return {
            "service_id": str(listing_data.service_id),
            "status": "featured",
            "message": "Service added to featured listings",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error featuring service: {str(e)}",
        )


@router.delete("/featured/{service_id}", response_model=dict)
async def remove_featured_listing(
    service_id: UUID,
    current_user: User = Depends(get_current_provider),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Remove service from featured listings.

    **Authorization**: Provider only

    **Path Parameters**: service_id (UUID)

    **Returns**: 200 Service unfeatured

    **Example**:
    ```
    DELETE /api/v1/subscriptions/featured/service-uuid
    ```
    """
    try:
        success = await SubscriptionService.remove_featured_listing(
            supabase, current_user.id, service_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to remove featured status",
            )

        return {
            "service_id": str(service_id),
            "status": "unfeatured",
            "message": "Service removed from featured listings",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error unfeaturing service: {str(e)}",
        )


@router.get("/history", response_model=dict)
async def get_subscription_history(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_provider),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Get subscription history.

    **Authorization**: Provider only

    **Query Parameters**: limit (default: 10, max: 50)

    **Returns**: 200 Subscription history

    **Example**:
    ```
    GET /api/v1/subscriptions/history?limit=20
    ```
    """
    try:
        subscriptions = await SubscriptionService.get_subscription_history(
            supabase, current_user.id, limit
        )

        return {
            "total": len(subscriptions),
            "items": [
                {
                    "id": str(s.id),
                    "plan": s.plan,
                    "status": s.status,
                    "price_per_month": s.price_per_month,
                    "start_date": s.start_date,
                    "end_date": s.end_date,
                    "created_at": s.created_at,
                }
                for s in subscriptions
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving history: {str(e)}",
        )


@router.get("/plans", response_model=PlanComparisonResponse)
async def get_plans():
    """
    Get all available plans comparison.

    **Authorization**: Public (no auth required)

    **Returns**: 200 Plan details

    **Example**:
    ```
    GET /api/v1/subscriptions/plans
    ```
    """
    try:
        plans = await SubscriptionService.get_all_plans()

        return PlanComparisonResponse(plans=plans)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving plans: {str(e)}",
        )

