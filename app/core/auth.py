"""
Supabase Authentication utilities for JWT token verification.
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

import jwt
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenPayload:
    """JWT token payload structure."""

    def __init__(
        self,
        sub: str,
        email: str,
        aud: str = "authenticated",
        role: str = "customer",
        user_metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        self.sub = UUID(sub)  # User ID
        self.email = email
        self.aud = aud
        self.role = role
        self.user_metadata = user_metadata or {}
        self.extra = kwargs

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenPayload":
        """Create TokenPayload from dictionary."""
        return cls(
            sub=data.get("sub"),
            email=data.get("email", ""),
            aud=data.get("aud", "authenticated"),
            role=data.get("role", "customer"),
            user_metadata=data.get("user_metadata", {}),
            **data
        )


class SupabaseAuthManager:
    """
    Manager for Supabase JWT token verification and user extraction.

    Handles:
    - JWT token verification using Supabase JWT secret
    - User ID and email extraction
    - Role extraction from token or user metadata
    - Token expiration validation
    """

    def __init__(self):
        self.supabase_url = settings.supabase_url
        self.supabase_key = settings.supabase_key
        self.jwt_secret = settings.supabase_jwt_secret or settings.secret_key
        self.algorithm = "HS256"

    def verify_token(self, token: str) -> TokenPayload:
        """
        Verify JWT token from Supabase.

        Args:
            token: JWT token string

        Returns:
            TokenPayload with decoded token data

        Raises:
            HTTPException: If token is invalid, expired, or verification fails
        """
        try:
            # Remove 'Bearer' prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            # Decode JWT token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.algorithm],
                audience="authenticated",
                options={"verify_exp": True}
            )

            logger.debug(f"Token verified for user: {payload.get('sub')}")
            return TokenPayload.from_dict(payload)

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def extract_user_info(self, token: str) -> Dict[str, Any]:
        """
        Extract user information from token.

        Args:
            token: JWT token string

        Returns:
            Dictionary with user_id, email, and role
        """
        payload = self.verify_token(token)
        return {
            "user_id": payload.sub,
            "email": payload.email,
            "role": payload.role,
            "user_metadata": payload.user_metadata,
        }

    @staticmethod
    def decode_token_without_verification(token: str) -> Dict[str, Any]:
        """
        Decode token without verification (for inspection only).

        WARNING: Use only for debugging or when you trust the token source.

        Args:
            token: JWT token string

        Returns:
            Decoded payload dictionary
        """
        try:
            if token.startswith("Bearer "):
                token = token[7:]

            payload = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=["HS256"]
            )
            return payload
        except Exception as e:
            logger.error(f"Error decoding token: {str(e)}")
            return {}


# Global instance
_auth_manager: Optional[SupabaseAuthManager] = None


def get_auth_manager() -> SupabaseAuthManager:
    """Get or create global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = SupabaseAuthManager()
    return _auth_manager


class RequireRole:
    """
    Role-based access control decorator.

    Usage:
        @app.get("/admin-only")
        async def admin_endpoint(current_user: User = Depends(get_current_user)):
            pass

    Or with role check:
        async def check_admin(current_user: User = Depends(get_current_user)):
            if current_user.role != "admin":
                raise HTTPException(status_code=403, detail="Admin access required")
            return current_user
    """

    def __init__(self, required_roles: list[str]):
        """
        Initialize role requirement.

        Args:
            required_roles: List of allowed roles
        """
        self.required_roles = required_roles

    async def __call__(self, current_user: "User") -> "User":  # noqa
        """Check if user has required role."""
        if current_user.role not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {', '.join(self.required_roles)}"
            )
        return current_user


def create_role_checker(*roles: str):
    """
    Create a role checker function for dependency injection.

    Usage:
        @app.get("/admin")
        async def admin_endpoint(
            current_user: User = Depends(get_current_user),
            _: None = Depends(create_role_checker("admin"))
        ):
            return current_user

    Args:
        roles: Allowed roles

    Returns:
        Dependency function
    """
    async def check_roles(current_user: "User") -> None:  # noqa
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(roles)}"
            )

    return Depends(check_roles)

