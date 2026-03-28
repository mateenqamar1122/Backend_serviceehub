"""
Authentication dependencies with Supabase Auth integration.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from supabase import Client

from app.core.auth import get_auth_manager, SupabaseAuthManager, TokenPayload
from app.db import get_supabase
from app.models import User, UserRole
from app.services import UserService

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_auth_manager_dep() -> SupabaseAuthManager:
    """Get Supabase auth manager."""
    return get_auth_manager()


async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    auth_manager: SupabaseAuthManager = Depends(get_auth_manager_dep),
    supabase: Client = Depends(get_supabase),
) -> User:
    """
    Get current authenticated user from JWT token.

    Verifies Supabase JWT token and retrieves user information.

    Args:
        credentials: HTTP Bearer token from Authorization header
        auth_manager: Supabase auth manager
        supabase: Supabase client

    Returns:
        Authenticated User object

    Raises:
        HTTPException 401: If token is invalid or expired
        HTTPException 404: If user not found in database
    """
    token = credentials.credentials

    # Verify token and extract payload
    token_payload: TokenPayload = auth_manager.verify_token(token)

    logger.debug(f"Token verified for user: {token_payload.sub}")

    # Get user from database
    user = await UserService.get_user_by_id(supabase, token_payload.sub)

    if not user:
        logger.warning(f"User not found: {token_payload.sub}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify user is active
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {token_payload.sub}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Update role from token if available (token takes precedence)
    if token_payload.role and token_payload.role in UserRole.ALL_ROLES:
        user.role = token_payload.role

    logger.debug(f"User authenticated: {user.email} (role: {user.role})")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user.

    Additional safety check for active status.

    Args:
        current_user: Current authenticated user

    Returns:
        Active user

    Raises:
        HTTPException 403: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return current_user


async def get_current_customer(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current user and verify customer role.

    Args:
        current_user: Current authenticated user

    Returns:
        User with customer role

    Raises:
        HTTPException 403: If user is not a customer
    """
    if current_user.role != UserRole.CUSTOMER and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires customer role",
        )
    return current_user


async def get_current_provider(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current user and verify provider role.

    Args:
        current_user: Current authenticated user

    Returns:
        User with provider role

    Raises:
        HTTPException 403: If user is not a provider
    """
    if current_user.role != UserRole.PROVIDER and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires provider role",
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current user and verify admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        User with admin role

    Raises:
        HTTPException 403: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthCredentials] = Depends(HTTPBearer(auto_error=False)),
    auth_manager: SupabaseAuthManager = Depends(get_auth_manager_dep),
    supabase: Client = Depends(get_supabase),
) -> Optional[User]:
    """
    Get optional authenticated user (does not require authentication).

    Useful for endpoints that work for both authenticated and anonymous users.

    Args:
        credentials: Optional HTTP Bearer token
        auth_manager: Supabase auth manager
        supabase: Supabase client

    Returns:
        User object if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, auth_manager, supabase)
    except HTTPException:
        return None

