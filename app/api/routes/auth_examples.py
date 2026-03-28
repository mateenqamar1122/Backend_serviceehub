"""
Example routes demonstrating Supabase Auth integration.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_customer,
    get_current_provider,
    get_current_admin,
    get_optional_user,
)
from app.models import User

router = APIRouter(prefix="/auth", tags=["authentication-examples"])


@router.get("/me", response_model=dict)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get current authenticated user profile.

    **Protected Route**: Requires valid JWT token

    Returns:
        User profile information
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }


@router.get("/me/active", response_model=dict)
async def get_active_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get current active user profile.

    **Protected Route**: Requires valid JWT token and active status

    Returns:
        User profile information
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "role": current_user.role,
    }


@router.get("/me/customer", response_model=dict)
async def get_customer_profile(
    current_user: User = Depends(get_current_customer),
) -> dict:
    """
    Get current customer profile.

    **Protected Route**: Requires customer or admin role

    Returns:
        Customer profile information
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "message": "Welcome, customer!",
    }


@router.get("/me/provider", response_model=dict)
async def get_provider_profile(
    current_user: User = Depends(get_current_provider),
) -> dict:
    """
    Get current provider profile.

    **Protected Route**: Requires provider or admin role

    Returns:
        Provider profile information
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "message": "Welcome, provider!",
    }


@router.get("/me/admin", response_model=dict)
async def get_admin_profile(
    current_user: User = Depends(get_current_admin),
) -> dict:
    """
    Get current admin profile.

    **Protected Route**: Requires admin role

    Returns:
        Admin profile information
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "message": "Welcome, admin!",
    }


@router.get("/info", response_model=dict)
async def get_user_info(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get detailed current user information.

    **Protected Route**: Requires authentication

    Returns:
        Detailed user information including all fields
    """
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "rating": current_user.rating,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None,
    }


@router.get("/verify-role", response_model=dict)
async def verify_user_role(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Verify current user role.

    **Protected Route**: Requires authentication

    Returns:
        User role information
    """
    role_permissions = {
        "customer": ["browse_services", "create_bookings", "leave_reviews"],
        "provider": ["create_services", "manage_bookings", "view_ratings"],
        "admin": ["manage_users", "manage_services", "manage_bookings", "view_analytics"],
    }

    return {
        "user_id": str(current_user.id),
        "role": current_user.role,
        "permissions": role_permissions.get(current_user.role, []),
    }


@router.get("/optional-info", response_model=dict)
async def get_optional_user_info(
    current_user: User = Depends(get_optional_user),
) -> dict:
    """
    Get user information if authenticated, otherwise return public response.

    **Semi-Protected Route**: Works with or without authentication

    Returns:
        User information if authenticated, else public data
    """
    if current_user:
        return {
            "authenticated": True,
            "user_id": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role,
        }
    else:
        return {
            "authenticated": False,
            "message": "Browse as guest",
        }


@router.get("/status", response_model=dict)
async def check_auth_status(
    current_user: User = Depends(get_optional_user),
) -> dict:
    """
    Check authentication status.

    Works for both authenticated and anonymous requests.

    Returns:
        Authentication status
    """
    if current_user:
        return {
            "status": "authenticated",
            "user_id": str(current_user.id),
            "role": current_user.role,
            "active": current_user.is_active,
        }
    else:
        return {
            "status": "anonymous",
            "message": "Not authenticated",
        }

