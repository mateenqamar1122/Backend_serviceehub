"""
Service endpoints using Supabase.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from app.api.dependencies import get_current_active_user
from app.db import get_supabase
from app.models import User, Service
from app.schemas import ServiceCreate, ServiceUpdate, ServiceResponse, ServiceListResponse
from app.services import ServiceService

router = APIRouter(prefix="/services", tags=["services"])


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> ServiceResponse:
    """Create a new service."""
    service = await ServiceService.create_service(
        supabase, service_data, current_user.id
    )
    return service


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: UUID,
    supabase: Client = Depends(get_supabase),
) -> ServiceResponse:
    """Get service details by ID."""
    service = await ServiceService.get_service_by_id(supabase, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )
    return service


@router.get("/", response_model=ServiceListResponse)
async def list_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: str = Query(None),
    search: str = Query(None),
    supabase: Client = Depends(get_supabase),
) -> ServiceListResponse:
    """
    List services with filters.

    Query parameters:
    - skip: Number of services to skip (default: 0)
    - limit: Number of services to return (default: 10, max: 100)
    - category: Filter by category
    - search: Search in title and description
    """
    if category:
        services = await ServiceService.get_services_by_category(
            supabase, category, skip=skip, limit=limit
        )
    elif search:
        services = await ServiceService.search_services(
            supabase, search, skip=skip, limit=limit
        )
    else:
        services = await ServiceService.get_all_services(
            supabase, skip=skip, limit=limit
        )

    total = await ServiceService.get_service_count(supabase)

    return ServiceListResponse(
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
        items=services,
    )


@router.get("/provider/{provider_id}", response_model=ServiceListResponse)
async def list_provider_services(
    provider_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    supabase: Client = Depends(get_supabase),
) -> ServiceListResponse:
    """Get all services from a provider."""
    services = await ServiceService.get_services_by_provider(
        supabase, provider_id, skip=skip, limit=limit
    )
    total = len(services)

    return ServiceListResponse(
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
        items=services,
    )


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: UUID,
    service_data: ServiceUpdate,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> ServiceResponse:
    """Update a service (only by provider)."""
    service = await ServiceService.get_service_by_id(supabase, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    if service.provider_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this service",
        )

    updated_service = await ServiceService.update_service(
        supabase, service_id, service_data
    )
    return updated_service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: UUID,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> None:
    """Delete a service (only by provider)."""
    service = await ServiceService.get_service_by_id(supabase, service_id)
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    if service.provider_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this service",
        )

    await ServiceService.delete_service(supabase, service_id)

