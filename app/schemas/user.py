"""
User schemas for request/response validation.
"""
from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """User update schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None


class UserResponse(UserBase):
    """User response schema."""
    id: UUID
    is_active: bool
    is_verified: bool
    rating: Optional[int] = None
    profile_picture_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """Detailed user response schema."""
    pass


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: str
    exp: int
    iat: int
    type: str = "access"

