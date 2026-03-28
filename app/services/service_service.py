"""
Service business logic using Supabase.
"""
from typing import Optional, List
from uuid import UUID

from supabase import Client

from app.models import Service
from app.schemas import ServiceCreate, ServiceUpdate


class ServiceService:
    """Service service for Supabase database operations."""

    @staticmethod
    async def create_service(
        supabase: Client,
        service_data: ServiceCreate,
        provider_id: UUID
    ) -> Service:
        """Create a new service."""
        response = supabase.table("services").insert({
            "provider_id": str(provider_id),
            "title": service_data.title,
            "description": service_data.description,
            "category": service_data.category,
            "price_per_hour": service_data.price_per_hour,
            "location": service_data.location,
            "tags": service_data.tags,
            "is_available": True,
        }).execute()

        if response.data:
            return Service(**response.data[0])
        raise ValueError("Failed to create service")

    @staticmethod
    async def get_service_by_id(
        supabase: Client,
        service_id: UUID
    ) -> Optional[Service]:
        """Get service by ID."""
        response = supabase.table("services").select("*").eq("id", str(service_id)).execute()

        if response.data and len(response.data) > 0:
            return Service(**response.data[0])
        return None

    @staticmethod
    async def get_services_by_provider(
        supabase: Client,
        provider_id: UUID,
        skip: int = 0,
        limit: int = 10
    ) -> List[Service]:
        """Get all services from a provider."""
        response = supabase.table("services").select("*").eq(
            "provider_id", str(provider_id)
        ).range(skip, skip + limit - 1).execute()

        return [Service(**service) for service in response.data]

    @staticmethod
    async def get_services_by_category(
        supabase: Client,
        category: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[Service]:
        """Get services by category."""
        response = supabase.table("services").select("*").eq(
            "category", category
        ).eq("is_available", True).range(skip, skip + limit - 1).execute()

        return [Service(**service) for service in response.data]

    @staticmethod
    async def get_all_services(
        supabase: Client,
        skip: int = 0,
        limit: int = 10
    ) -> List[Service]:
        """Get all available services."""
        response = supabase.table("services").select("*").eq(
            "is_available", True
        ).range(skip, skip + limit - 1).execute()

        return [Service(**service) for service in response.data]

    @staticmethod
    async def search_services(
        supabase: Client,
        query: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[Service]:
        """Search services by title or description using ilike."""
        # Supabase supports 'ilike' for case-insensitive search
        response = supabase.table("services").select("*").ilike(
            "title", f"%{query}%"
        ).eq("is_available", True).range(skip, skip + limit - 1).execute()

        return [Service(**service) for service in response.data]

    @staticmethod
    async def update_service(
        supabase: Client,
        service_id: UUID,
        service_data: ServiceUpdate
    ) -> Optional[Service]:
        """Update service information."""
        update_data = service_data.dict(exclude_unset=True)

        response = supabase.table("services").update(update_data).eq(
            "id", str(service_id)
        ).execute()

        if response.data and len(response.data) > 0:
            return Service(**response.data[0])
        return None

    @staticmethod
    async def delete_service(
        supabase: Client,
        service_id: UUID
    ) -> bool:
        """Delete service."""
        response = supabase.table("services").delete().eq("id", str(service_id)).execute()

        return bool(response.data)

    @staticmethod
    async def get_service_count(supabase: Client) -> int:
        """Get total count of services."""
        response = supabase.table("services").select("id", count="exact").execute()
        return response.count or 0

