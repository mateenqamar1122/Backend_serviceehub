"""
User model for Supabase.
"""
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from app.db.base import BaseModel


class UserRole:
    """User roles for role-based access control."""
    CUSTOMER = "customer"
    PROVIDER = "provider"
    ADMIN = "admin"

    ALL_ROLES = [CUSTOMER, PROVIDER, ADMIN]


class User(BaseModel):
    """User model representing a user in the system."""

    def __init__(
        self,
        id: Optional[UUID] = None,
        email: str = "",
        username: str = "",
        hashed_password: str = "",
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        bio: Optional[str] = None,
        profile_picture_url: Optional[str] = None,
        is_active: bool = True,
        is_verified: bool = False,
        rating: Optional[int] = None,
        role: str = UserRole.CUSTOMER,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        **kwargs,
    ):
        """Initialize User model."""
        super().__init__(**kwargs)
        self.id = id
        self.email = email
        self.username = username
        self.hashed_password = hashed_password
        self.first_name = first_name
        self.last_name = last_name
        self.bio = bio
        self.profile_picture_url = profile_picture_url
        self.is_active = is_active
        self.is_verified = is_verified
        self.rating = rating
        self.role = role
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username}, role={self.role})>"

