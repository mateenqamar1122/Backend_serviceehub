"""
User service business logic using Supabase.
"""
from typing import Optional, List
from uuid import UUID

from supabase import Client

from app.models import User
from app.schemas import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password


class UserService:
    """User service for Supabase database operations."""

    @staticmethod
    async def create_user(
        supabase: Client,
        user_data: UserCreate
    ) -> User:
        """Create a new user."""
        hashed_password = hash_password(user_data.password)

        response = supabase.table("users").insert({
            "email": user_data.email,
            "username": user_data.username,
            "hashed_password": hashed_password,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "bio": user_data.bio,
            "is_active": True,
            "is_verified": False,
        }).execute()

        if response.data:
            return User(**response.data[0])
        raise ValueError("Failed to create user")

    @staticmethod
    async def get_user_by_id(
        supabase: Client,
        user_id: UUID
    ) -> Optional[User]:
        """Get user by ID."""
        response = supabase.table("users").select("*").eq("id", str(user_id)).execute()

        if response.data and len(response.data) > 0:
            return User(**response.data[0])
        return None

    @staticmethod
    async def get_user_by_email(
        supabase: Client,
        email: str
    ) -> Optional[User]:
        """Get user by email."""
        response = supabase.table("users").select("*").eq("email", email).execute()

        if response.data and len(response.data) > 0:
            return User(**response.data[0])
        return None

    @staticmethod
    async def get_user_by_username(
        supabase: Client,
        username: str
    ) -> Optional[User]:
        """Get user by username."""
        response = supabase.table("users").select("*").eq("username", username).execute()

        if response.data and len(response.data) > 0:
            return User(**response.data[0])
        return None

    @staticmethod
    async def get_all_users(
        supabase: Client,
        skip: int = 0,
        limit: int = 10
    ) -> List[User]:
        """Get all users with pagination."""
        response = supabase.table("users").select("*").range(skip, skip + limit - 1).execute()

        return [User(**user) for user in response.data]

    @staticmethod
    async def update_user(
        supabase: Client,
        user_id: UUID,
        user_data: UserUpdate
    ) -> Optional[User]:
        """Update user information."""
        update_data = user_data.dict(exclude_unset=True)

        response = supabase.table("users").update(update_data).eq("id", str(user_id)).execute()

        if response.data and len(response.data) > 0:
            return User(**response.data[0])
        return None

    @staticmethod
    async def delete_user(
        supabase: Client,
        user_id: UUID
    ) -> bool:
        """Soft delete user by marking as inactive."""
        response = supabase.table("users").update({"is_active": False}).eq("id", str(user_id)).execute()

        return bool(response.data)

    @staticmethod
    async def verify_password(
        user: User,
        password: str
    ) -> bool:
        """Verify user password."""
        return verify_password(password, user.hashed_password)

    @staticmethod
    async def update_password(
        supabase: Client,
        user_id: UUID,
        new_password: str
    ) -> Optional[User]:
        """Update user password."""
        hashed_password = hash_password(new_password)

        response = supabase.table("users").update(
            {"hashed_password": hashed_password}
        ).eq("id", str(user_id)).execute()

        if response.data and len(response.data) > 0:
            return User(**response.data[0])
        return None


