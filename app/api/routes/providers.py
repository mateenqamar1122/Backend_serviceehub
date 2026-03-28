"""
Provider search and discovery endpoints.

Features:
- Search providers by name, category, location
- Filter by rating, minimum reviews, availability
- Join with provider profiles and services
- Optimized response with aggregated data
"""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from app.api.dependencies import get_current_active_user, get_optional_user
from app.db import get_supabase
from app.models import User

router = APIRouter(prefix="/providers", tags=["providers"])


# ============================================================================
# Response Models (simplified for provider discovery)
# ============================================================================

class ProviderService:
    """Lightweight service info for provider listing."""
    def __init__(self, id: str, title: str, category: str, price_per_hour: float, rating: float):
        self.id = id
        self.title = title
        self.category = category
        self.price_per_hour = price_per_hour
        self.rating = rating


class ProviderSummary:
    """Provider summary for list view."""
    def __init__(
        self,
        id: str,
        username: str,
        first_name: str,
        last_name: str,
        profile_picture_url: str,
        bio: str,
        average_rating: float,
        total_reviews: int,
        city: str,
        state: str,
        country: str,
        is_verified: bool,
        response_time_minutes: int,
        total_services: int,
        services: List[ProviderService],
    ):
        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.profile_picture_url = profile_picture_url
        self.bio = bio
        self.average_rating = average_rating
        self.total_reviews = total_reviews
        self.city = city
        self.state = state
        self.country = country
        self.is_verified = is_verified
        self.response_time_minutes = response_time_minutes
        self.total_services = total_services
        self.services = services


class ProviderDetail:
    """Full provider details for detail view."""
    def __init__(
        self,
        id: str,
        username: str,
        email: str,
        first_name: str,
        last_name: str,
        profile_picture_url: str,
        bio: str,
        phone_number: str,
        average_rating: float,
        total_reviews: int,
        total_bookings: int,
        completion_rate: float,
        city: str,
        state: str,
        country: str,
        postal_code: str,
        is_verified: bool,
        verified_at: str,
        years_of_experience: int,
        certifications: List[str],
        response_time_minutes: int,
        cancellation_rate: float,
        services: List[dict],
    ):
        self.id = id
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.profile_picture_url = profile_picture_url
        self.bio = bio
        self.phone_number = phone_number
        self.average_rating = average_rating
        self.total_reviews = total_reviews
        self.total_bookings = total_bookings
        self.completion_rate = completion_rate
        self.city = city
        self.state = state
        self.country = country
        self.postal_code = postal_code
        self.is_verified = is_verified
        self.verified_at = verified_at
        self.years_of_experience = years_of_experience
        self.certifications = certifications
        self.response_time_minutes = response_time_minutes
        self.cancellation_rate = cancellation_rate
        self.services = services


# ============================================================================
# Search & Discovery Endpoints
# ============================================================================

@router.get("/", response_model=dict)
async def get_providers(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None, min_length=1),
    category: str = Query(None),
    location: str = Query(None),
    min_rating: float = Query(0, ge=0, le=5),
    min_reviews: int = Query(0, ge=0),
    verified_only: bool = Query(False),
    sort_by: str = Query("rating", regex="^(rating|reviews|name)$"),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Get providers with search, filtering, and sorting.

    **Query Parameters**:
    - skip: Number of providers to skip (default: 0)
    - limit: Number of providers to return (default: 10, max: 100)
    - search: Search by username or company name
    - category: Filter by service category
    - location: Filter by city/country
    - min_rating: Minimum average rating (0-5)
    - min_reviews: Minimum number of reviews
    - verified_only: Only verified providers (default: False)
    - sort_by: Sort by rating, reviews, or name

    **Returns**: Paginated list of provider summaries with their services

    **Example**:
    ```
    GET /api/v1/providers?category=cleaning&location=New York&min_rating=4.5&limit=20
    ```
    """
    try:
        # Build base query for users with provider role
        providers_query = supabase.table("users").select(
            "id, username, first_name, last_name, profile_picture_url, bio, "
            "average_rating, total_reviews, city, state, country, created_at"
        ).eq("role", "provider").eq("is_active", True)

        # Apply rating filter
        if min_rating > 0:
            providers_query = providers_query.gte("average_rating", min_rating)

        # Apply reviews filter
        if min_reviews > 0:
            providers_query = providers_query.gte("total_reviews", min_reviews)

        # Apply verified filter
        if verified_only:
            providers_query = providers_query.eq("is_verified", True)

        # Apply search filter (username or first/last name)
        if search:
            search_lower = search.lower()
            # Note: Supabase doesn't support complex OR in simple filter
            # Client-side filtering needed or use full-text search
            providers_response = providers_query.execute()
            providers_data = [
                p for p in providers_response.data
                if (search_lower in p.get("username", "").lower() or
                    search_lower in p.get("first_name", "").lower() or
                    search_lower in p.get("last_name", "").lower())
            ]
        else:
            providers_response = providers_query.execute()
            providers_data = providers_response.data

        # Apply location filter
        if location:
            location_lower = location.lower()
            providers_data = [
                p for p in providers_data
                if (location_lower in p.get("city", "").lower() or
                    location_lower in p.get("state", "").lower() or
                    location_lower in p.get("country", "").lower())
            ]

        # Apply sorting
        if sort_by == "rating":
            providers_data.sort(
                key=lambda x: (x.get("average_rating", 0), x.get("total_reviews", 0)),
                reverse=True
            )
        elif sort_by == "reviews":
            providers_data.sort(
                key=lambda x: x.get("total_reviews", 0),
                reverse=True
            )
        elif sort_by == "name":
            providers_data.sort(
                key=lambda x: (
                    x.get("first_name", "") + " " + x.get("last_name", "")
                ).lower()
            )

        # Get total count before pagination
        total = len(providers_data)

        # Apply pagination
        paginated_data = providers_data[skip : skip + limit]

        # Get services and provider profiles for each provider
        providers_list = []
        for provider_data in paginated_data:
            provider_id = provider_data["id"]

            # Get provider profile
            profile_response = supabase.table("provider_profiles").select("*").eq(
                "provider_id", provider_id
            ).execute()
            profile = profile_response.data[0] if profile_response.data else {}

            # Get services
            services_response = supabase.table("services").select(
                "id, title, category, price_per_hour, average_rating"
            ).eq("provider_id", provider_id).eq("status", "active").limit(5).execute()

            services = [
                ProviderService(
                    id=str(s["id"]),
                    title=s["title"],
                    category=s["category"],
                    price_per_hour=s["price_per_hour"],
                    rating=s.get("average_rating", 0),
                )
                for s in services_response.data
            ]

            # Filter by category if specified
            if category:
                has_category = any(s.category == category for s in services)
                if not has_category:
                    continue

            provider_summary = ProviderSummary(
                id=str(provider_data["id"]),
                username=provider_data["username"],
                first_name=provider_data.get("first_name", ""),
                last_name=provider_data.get("last_name", ""),
                profile_picture_url=provider_data.get("profile_picture_url", ""),
                bio=provider_data.get("bio", ""),
                average_rating=provider_data.get("average_rating", 0),
                total_reviews=provider_data.get("total_reviews", 0),
                city=provider_data.get("city", ""),
                state=provider_data.get("state", ""),
                country=provider_data.get("country", ""),
                is_verified=profile.get("is_verified", False),
                response_time_minutes=profile.get("response_time_minutes", 0),
                total_services=profile.get("total_services", 0),
                services=[
                    {
                        "id": s.id,
                        "title": s.title,
                        "category": s.category,
                        "price_per_hour": s.price_per_hour,
                        "rating": s.rating,
                    }
                    for s in services
                ],
            )
            providers_list.append(provider_summary)

        # Re-apply pagination after category filtering
        if category:
            total = len(providers_list)
            providers_list = providers_list[skip : skip + limit]

        # Convert to dict for response
        providers_dict = [
            {
                "id": p.id,
                "username": p.username,
                "name": f"{p.first_name} {p.last_name}".strip(),
                "profile_picture_url": p.profile_picture_url,
                "bio": p.bio,
                "average_rating": p.average_rating,
                "total_reviews": p.total_reviews,
                "location": f"{p.city}, {p.country}".strip(","),
                "is_verified": p.is_verified,
                "response_time_minutes": p.response_time_minutes,
                "total_services": p.total_services,
                "services_preview": p.services[:3],  # Show only 3 services
            }
            for p in providers_list
        ]

        return {
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "page_size": limit,
            "items": providers_dict,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching providers: {str(e)}",
        )


@router.get("/{provider_id}", response_model=dict)
async def get_provider_detail(
    provider_id: UUID,
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Get detailed provider profile with all services.

    **Path Parameters**:
    - provider_id: Provider UUID

    **Returns**:
    - Provider details
    - All active services
    - Professional information
    - Ratings and statistics

    **Example**:
    ```
    GET /api/v1/providers/uuid
    ```
    """
    try:
        # Get user profile
        user_response = supabase.table("users").select("*").eq(
            "id", str(provider_id)
        ).eq("role", "provider").execute()

        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Provider not found",
            )

        user_data = user_response.data[0]

        # Get provider profile
        profile_response = supabase.table("provider_profiles").select("*").eq(
            "provider_id", str(provider_id)
        ).execute()
        profile_data = profile_response.data[0] if profile_response.data else {}

        # Get all services
        services_response = supabase.table("services").select("*").eq(
            "provider_id", str(provider_id)
        ).eq("status", "active").execute()

        services = [
            {
                "id": str(s["id"]),
                "title": s["title"],
                "description": s["description"],
                "category": s["category"],
                "subcategory": s.get("subcategory", ""),
                "price_per_hour": s["price_per_hour"],
                "average_rating": s.get("average_rating", 0),
                "total_reviews": s.get("total_reviews", 0),
                "total_bookings": s.get("total_bookings", 0),
                "thumbnail_url": s.get("thumbnail_url", ""),
                "is_available": s["is_available"],
            }
            for s in services_response.data
        ]

        # Get recent reviews
        reviews_response = supabase.table("reviews").select(
            "id, rating, comment, reviewer_id, created_at"
        ).eq("reviewee_id", str(provider_id)).order(
            "created_at", desc=True
        ).limit(5).execute()

        provider_detail = {
            "id": str(user_data["id"]),
            "username": user_data["username"],
            "email": user_data.get("email", ""),
            "name": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip(),
            "profile_picture_url": user_data.get("profile_picture_url", ""),
            "bio": user_data.get("bio", ""),
            "phone_number": user_data.get("phone_number", ""),
            "average_rating": user_data.get("average_rating", 0),
            "total_reviews": user_data.get("total_reviews", 0),
            "total_bookings": user_data.get("total_bookings", 0),
            "completion_rate": user_data.get("completion_rate", 0),
            "location": {
                "city": user_data.get("city", ""),
                "state": user_data.get("state", ""),
                "country": user_data.get("country", ""),
                "postal_code": user_data.get("postal_code", ""),
            },
            "verification": {
                "is_verified": profile_data.get("is_verified", False),
                "verified_at": profile_data.get("verified_at", ""),
            },
            "professional": {
                "years_of_experience": profile_data.get("years_of_experience", 0),
                "certifications": profile_data.get("certifications", []),
                "response_time_minutes": profile_data.get("response_time_minutes", 0),
                "cancellation_rate": profile_data.get("cancellation_rate", 0),
                "business_category": profile_data.get("business_category", ""),
            },
            "services": services,
            "recent_reviews": [
                {
                    "id": str(r["id"]),
                    "rating": r["rating"],
                    "comment": r["comment"],
                    "created_at": r["created_at"],
                }
                for r in reviews_response.data
            ],
        }

        return provider_detail

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching provider details: {str(e)}",
        )


@router.get("/search/by-category", response_model=dict)
async def search_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    min_rating: float = Query(0, ge=0, le=5),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Search providers by service category.

    **Query Parameters**:
    - category: Service category (required)
    - skip: Pagination offset
    - limit: Results per page
    - min_rating: Minimum provider rating

    **Returns**: Providers sorted by rating with services in category

    **Example**:
    ```
    GET /api/v1/providers/search/by-category?category=cleaning&min_rating=4.0
    ```
    """
    try:
        # Get all services in category
        services_response = supabase.table("services").select(
            "id, provider_id, title, price_per_hour, average_rating"
        ).eq("category", category).eq("status", "active").execute()

        if not services_response.data:
            return {"total": 0, "page": 1, "page_size": limit, "items": []}

        # Get unique provider IDs
        provider_ids = list(set(s["provider_id"] for s in services_response.data))

        # Get provider details
        providers_data = []
        for pid in provider_ids:
            user_response = supabase.table("users").select(
                "id, username, first_name, last_name, profile_picture_url, bio, "
                "average_rating, total_reviews, city, state, country"
            ).eq("id", pid).eq("role", "provider").gte("average_rating", min_rating).execute()

            if user_response.data:
                providers_data.append(user_response.data[0])

        # Sort by rating
        providers_data.sort(
            key=lambda x: (x.get("average_rating", 0), x.get("total_reviews", 0)),
            reverse=True
        )

        total = len(providers_data)
        paginated = providers_data[skip : skip + limit]

        # Build response
        items = []
        for provider in paginated:
            pid = provider["id"]

            # Get services in category for this provider
            category_services = [
                s for s in services_response.data
                if s["provider_id"] == pid
            ]

            profile_response = supabase.table("provider_profiles").select(
                "is_verified, response_time_minutes, total_services"
            ).eq("provider_id", pid).execute()
            profile = profile_response.data[0] if profile_response.data else {}

            items.append({
                "id": str(provider["id"]),
                "username": provider["username"],
                "name": f"{provider.get('first_name', '')} {provider.get('last_name', '')}".strip(),
                "profile_picture_url": provider.get("profile_picture_url", ""),
                "bio": provider.get("bio", ""),
                "average_rating": provider.get("average_rating", 0),
                "total_reviews": provider.get("total_reviews", 0),
                "location": f"{provider.get('city', '')}, {provider.get('country', '')}".strip(","),
                "is_verified": profile.get("is_verified", False),
                "services_in_category": len(category_services),
                "avg_price": sum(s["price_per_hour"] for s in category_services) / len(category_services) if category_services else 0,
            })

        return {
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "page_size": limit,
            "category": category,
            "items": items,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching providers by category: {str(e)}",
        )


@router.get("/search/by-location", response_model=dict)
async def search_by_location(
    location: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: str = Query(None),
    min_rating: float = Query(0, ge=0, le=5),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """
    Search providers by location.

    **Query Parameters**:
    - location: City or country (required)
    - category: Filter by service category (optional)
    - skip: Pagination offset
    - limit: Results per page
    - min_rating: Minimum provider rating

    **Returns**: Providers in location sorted by rating

    **Example**:
    ```
    GET /api/v1/providers/search/by-location?location=New York&category=cleaning
    ```
    """
    try:
        location_lower = location.lower()

        # Get providers in location
        users_response = supabase.table("users").select(
            "id, username, first_name, last_name, profile_picture_url, bio, "
            "average_rating, total_reviews, city, state, country"
        ).eq("role", "provider").eq("is_active", True).gte(
            "average_rating", min_rating
        ).execute()

        # Filter by location
        providers_data = [
            u for u in users_response.data
            if (location_lower in u.get("city", "").lower() or
                location_lower in u.get("state", "").lower() or
                location_lower in u.get("country", "").lower())
        ]

        # If category specified, filter providers with services in that category
        if category:
            providers_with_category = []
            for provider in providers_data:
                services_response = supabase.table("services").select("id").eq(
                    "provider_id", provider["id"]
                ).eq("category", category).eq("status", "active").limit(1).execute()

                if services_response.data:
                    providers_with_category.append(provider)

            providers_data = providers_with_category

        # Sort by rating
        providers_data.sort(
            key=lambda x: (x.get("average_rating", 0), x.get("total_reviews", 0)),
            reverse=True
        )

        total = len(providers_data)
        paginated = providers_data[skip : skip + limit]

        # Build response
        items = []
        for provider in paginated:
            pid = provider["id"]

            profile_response = supabase.table("provider_profiles").select(
                "is_verified, response_time_minutes, total_services"
            ).eq("provider_id", pid).execute()
            profile = profile_response.data[0] if profile_response.data else {}

            items.append({
                "id": str(provider["id"]),
                "username": provider["username"],
                "name": f"{provider.get('first_name', '')} {provider.get('last_name', '')}".strip(),
                "profile_picture_url": provider.get("profile_picture_url", ""),
                "bio": provider.get("bio", ""),
                "average_rating": provider.get("average_rating", 0),
                "total_reviews": provider.get("total_reviews", 0),
                "location": f"{provider.get('city', '')}, {provider.get('country', '')}".strip(","),
                "is_verified": profile.get("is_verified", False),
                "total_services": profile.get("total_services", 0),
            })

        return {
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "page_size": limit,
            "location": location,
            "category": category,
            "items": items,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching providers by location: {str(e)}",
        )

