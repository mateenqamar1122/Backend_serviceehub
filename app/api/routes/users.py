"""
User endpoints using Supabase.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.api.dependencies import get_current_active_user
from app.db import get_supabase
from app.models import User
from app.schemas import UserResponse, UserUpdate, UserDetailResponse
from app.services import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserDetailResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserDetailResponse:
    """Get current user profile."""
    return current_user


@router.put("/me", response_model=UserDetailResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase),
) -> UserDetailResponse:
    """Update current user profile."""
    updated_user = await UserService.update_user(supabase, current_user.id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return updated_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    supabase: Client = Depends(get_supabase),
) -> UserResponse:
    """Get user profile by ID."""
    user = await UserService.get_user_by_id(supabase, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 10,
    supabase: Client = Depends(get_supabase),
) -> list[UserResponse]:
    """List all users with pagination."""
    if limit > 100:
        limit = 100
    users = await UserService.get_all_users(supabase, skip=skip, limit=limit)
    return users

