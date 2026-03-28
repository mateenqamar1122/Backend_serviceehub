"""
Authentication endpoints (login, register, refresh token) using Supabase.
"""
from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.security import create_access_token, create_refresh_token, verify_password, decode_token
from app.db import get_supabase
from app.models import User
from app.schemas import UserCreate, TokenResponse
from app.services import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    supabase: Client = Depends(get_supabase),
) -> TokenResponse:
    """
    Register a new user.

    Args:
        user_data: User registration data
        supabase: Supabase client

    Returns:
        TokenResponse with access and refresh tokens

    Raises:
        HTTPException: If email or username already exists
    """
    # Check if email already exists
    existing_email = await UserService.get_user_by_email(supabase, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username already exists
    existing_username = await UserService.get_user_by_username(supabase, user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create user
    user = await UserService.create_user(supabase, user_data)

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    email: str,
    password: str,
    supabase: Client = Depends(get_supabase),
) -> TokenResponse:
    """
    Login user and return tokens.

    Args:
        email: User email
        password: User password
        supabase: Supabase client

    Returns:
        TokenResponse with access and refresh tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    user = await UserService.get_user_by_email(supabase, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not await UserService.verify_password(user, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    supabase: Client = Depends(get_supabase),
) -> TokenResponse:
    """
    Refresh access token using refresh token.

    Args:
        refresh_token: Refresh token
        supabase: Supabase client

    Returns:
        TokenResponse with new access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = await UserService.get_user_by_id(supabase, UUID(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Create new access token
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )

