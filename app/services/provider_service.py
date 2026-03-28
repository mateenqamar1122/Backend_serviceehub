"""
Provider service business logic using Supabase.

Handles:
- Provider search and filtering
- Provider profile retrieval
- Provider statistics aggregation
- Service discovery
"""
from typing import Optional, List
from uuid import UUID

from supabase import Client


class ProviderService:
    """Provider service for database operations."""

    @staticmethod
    async def search_providers(
        supabase: Client,
        search_query: Optional[str] = None,
        category: Optional[str] = None,
        location: Optional[str] = None,
        min_rating: float = 0,
        min_reviews: int = 0,
        verified_only: bool = False,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[List[dict], int]:
        """
        Search providers with multiple filters.

        Args:
            supabase: Supabase client
            search_query: Search by username or name
            category: Filter by service category
            location: Filter by city/country
            min_rating: Minimum average rating
            min_reviews: Minimum number of reviews
            verified_only: Only show verified providers
            skip: Pagination offset
            limit: Results per page

        Returns:
            Tuple of (providers list, total count)
        """
        # Get all active providers
        query = supabase.table("users").select(
            "id, username, first_name, last_name, profile_picture_url, bio, "
            "average_rating, total_reviews, city, state, country"
        ).eq("role", "provider").eq("is_active", True)

        if min_rating > 0:
            query = query.gte("average_rating", min_rating)

        if min_reviews > 0:
            query = query.gte("total_reviews", min_reviews)

        response = query.execute()
        providers_data = response.data or []

        # Client-side filtering
        filtered = providers_data

        # Search filter
        if search_query:
            search_lower = search_query.lower()
            filtered = [
                p for p in filtered
                if (search_lower in p.get("username", "").lower() or
                    search_lower in p.get("first_name", "").lower() or
                    search_lower in p.get("last_name", "").lower())
            ]

        # Location filter
        if location:
            location_lower = location.lower()
            filtered = [
                p for p in filtered
                if (location_lower in p.get("city", "").lower() or
                    location_lower in p.get("state", "").lower() or
                    location_lower in p.get("country", "").lower())
            ]

        # Verified filter
        if verified_only:
            verified_ids = set()
            profiles = supabase.table("provider_profiles").select(
                "provider_id"
            ).eq("is_verified", True).execute()
            verified_ids = set(p["provider_id"] for p in profiles.data or [])
            filtered = [p for p in filtered if p["id"] in verified_ids]

        # Category filter - requires checking services
        if category:
            providers_with_category = []
            for p in filtered:
                services = supabase.table("services").select("id").eq(
                    "provider_id", p["id"]
                ).eq("category", category).eq("status", "active").limit(1).execute()

                if services.data:
                    providers_with_category.append(p)

            filtered = providers_with_category

        # Sort by rating and reviews
        filtered.sort(
            key=lambda x: (x.get("average_rating", 0), x.get("total_reviews", 0)),
            reverse=True
        )

        total = len(filtered)
        paginated = filtered[skip : skip + limit]

        return paginated, total

    @staticmethod
    async def get_provider_profile(
        supabase: Client,
        provider_id: UUID,
    ) -> Optional[dict]:
        """
        Get full provider profile with services and reviews.

        Args:
            supabase: Supabase client
            provider_id: Provider UUID

        Returns:
            Provider profile dict or None
        """
        # Get user
        user_response = supabase.table("users").select("*").eq(
            "id", str(provider_id)
        ).eq("role", "provider").execute()

        if not user_response.data:
            return None

        user = user_response.data[0]

        # Get provider profile
        profile_response = supabase.table("provider_profiles").select("*").eq(
            "provider_id", str(provider_id)
        ).execute()
        profile = profile_response.data[0] if profile_response.data else {}

        # Get services
        services_response = supabase.table("services").select("*").eq(
            "provider_id", str(provider_id)
        ).eq("status", "active").execute()
        services = services_response.data or []

        # Get recent reviews
        reviews_response = supabase.table("reviews").select(
            "id, rating, comment, reviewer_id, created_at"
        ).eq("reviewee_id", str(provider_id)).order(
            "created_at", desc=True
        ).limit(10).execute()
        reviews = reviews_response.data or []

        return {
            "user": user,
            "profile": profile,
            "services": services,
            "reviews": reviews,
        }

    @staticmethod
    async def get_providers_by_category(
        supabase: Client,
        category: str,
        min_rating: float = 0,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[List[dict], int]:
        """
        Get providers offering services in a category.

        Args:
            supabase: Supabase client
            category: Service category
            min_rating: Minimum provider rating
            skip: Pagination offset
            limit: Results per page

        Returns:
            Tuple of (providers list, total count)
        """
        # Get services in category
        services_response = supabase.table("services").select(
            "provider_id, title, price_per_hour, average_rating"
        ).eq("category", category).eq("status", "active").execute()

        if not services_response.data:
            return [], 0

        # Get unique provider IDs
        provider_ids = list(set(s["provider_id"] for s in services_response.data))

        # Get provider details
        providers_data = []
        for pid in provider_ids:
            user_response = supabase.table("users").select("*").eq(
                "id", pid
            ).eq("role", "provider").gte("average_rating", min_rating).execute()

            if user_response.data:
                providers_data.append(user_response.data[0])

        # Sort by rating
        providers_data.sort(
            key=lambda x: (x.get("average_rating", 0), x.get("total_reviews", 0)),
            reverse=True
        )

        total = len(providers_data)
        paginated = providers_data[skip : skip + limit]

        return paginated, total

    @staticmethod
    async def get_providers_by_location(
        supabase: Client,
        location: str,
        category: Optional[str] = None,
        min_rating: float = 0,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[List[dict], int]:
        """
        Get providers in a location.

        Args:
            supabase: Supabase client
            location: City or country
            category: Filter by service category (optional)
            min_rating: Minimum provider rating
            skip: Pagination offset
            limit: Results per page

        Returns:
            Tuple of (providers list, total count)
        """
        location_lower = location.lower()

        # Get providers in location
        response = supabase.table("users").select("*").eq(
            "role", "provider"
        ).eq("is_active", True).gte("average_rating", min_rating).execute()

        # Filter by location
        providers_data = [
            u for u in response.data or []
            if (location_lower in u.get("city", "").lower() or
                location_lower in u.get("state", "").lower() or
                location_lower in u.get("country", "").lower())
        ]

        # Filter by category if provided
        if category:
            providers_with_category = []
            for provider in providers_data:
                services = supabase.table("services").select("id").eq(
                    "provider_id", provider["id"]
                ).eq("category", category).eq("status", "active").limit(1).execute()

                if services.data:
                    providers_with_category.append(provider)

            providers_data = providers_with_category

        # Sort by rating
        providers_data.sort(
            key=lambda x: (x.get("average_rating", 0), x.get("total_reviews", 0)),
            reverse=True
        )

        total = len(providers_data)
        paginated = providers_data[skip : skip + limit]

        return paginated, total

    @staticmethod
    async def get_top_providers(
        supabase: Client,
        limit: int = 10,
        min_reviews: int = 5,
    ) -> List[dict]:
        """
        Get top-rated providers.

        Args:
            supabase: Supabase client
            limit: Number of providers to return
            min_reviews: Minimum number of reviews

        Returns:
            List of top providers
        """
        response = supabase.table("users").select(
            "id, username, first_name, last_name, profile_picture_url, "
            "average_rating, total_reviews, city, country"
        ).eq("role", "provider").eq("is_active", True).gte(
            "total_reviews", min_reviews
        ).order("average_rating", desc=True).limit(limit).execute()

        return response.data or []

    @staticmethod
    async def get_verified_providers(
        supabase: Client,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[List[dict], int]:
        """
        Get verified providers.

        Args:
            supabase: Supabase client
            skip: Pagination offset
            limit: Results per page

        Returns:
            Tuple of (providers list, total count)
        """
        # Get verified provider IDs
        profiles_response = supabase.table("provider_profiles").select(
            "provider_id"
        ).eq("is_verified", True).execute()

        verified_ids = [p["provider_id"] for p in profiles_response.data or []]

        if not verified_ids:
            return [], 0

        # Get user details
        users_response = supabase.table("users").select(
            "id, username, first_name, last_name, profile_picture_url, "
            "average_rating, total_reviews, city, country"
        ).eq("role", "provider").eq("is_active", True).execute()

        # Filter verified users
        providers_data = [
            u for u in users_response.data or []
            if u["id"] in verified_ids
        ]

        # Sort by rating
        providers_data.sort(
            key=lambda x: (x.get("average_rating", 0), x.get("total_reviews", 0)),
            reverse=True
        )

        total = len(providers_data)
        paginated = providers_data[skip : skip + limit]

        return paginated, total

    @staticmethod
    async def get_provider_with_services(
        supabase: Client,
        provider_id: UUID,
    ) -> Optional[dict]:
        """
        Get provider with all services and statistics.

        Args:
            supabase: Supabase client
            provider_id: Provider UUID

        Returns:
            Provider dict with services or None
        """
        profile = await ProviderService.get_provider_profile(supabase, provider_id)

        if not profile:
            return None

        # Aggregate statistics from services
        services = profile["services"]

        stats = {
            "total_services": len(services),
            "avg_price": sum(s.get("price_per_hour", 0) for s in services) / len(services) if services else 0,
            "categories": list(set(s.get("category") for s in services if s.get("category"))),
        }

        profile["statistics"] = stats

        return profile

