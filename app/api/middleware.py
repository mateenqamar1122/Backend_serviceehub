"""
Middleware for authentication and request processing.
"""
import logging
import time
from typing import Callable, Optional

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.auth import get_auth_manager

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate authentication tokens on protected routes.

    Provides:
    - Token validation on protected endpoints
    - User context in request state
    - Automatic 401/403 responses for auth failures
    """

    # Routes that don't require authentication
    UNPROTECTED_ROUTES = {
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/health",
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Callable:
        """
        Process request and validate authentication if needed.

        Args:
            request: HTTP request
            call_next: Next middleware/endpoint

        Returns:
            Response
        """
        start_time = time.time()
        path = request.url.path

        # Skip auth check for unprotected routes
        if any(path.startswith(route) for route in self.UNPROTECTED_ROUTES):
            response = await call_next(request)
            process_time = time.time() - start_time
            logger.debug(f"{request.method} {path} - {response.status_code} ({process_time:.3f}s)")
            return response

        # Check authorization header for protected routes
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            logger.warning(f"Missing authorization header for {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            # Extract token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0] != "Bearer":
                logger.warning(f"Invalid auth header format for {path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authorization header format"},
                    headers={"WWW-Authenticate": "Bearer"},
                )

            token = parts[1]
            auth_manager = get_auth_manager()

            # Verify token
            token_payload = auth_manager.verify_token(token)

            # Add user info to request state
            request.state.user_id = token_payload.sub
            request.state.email = token_payload.email
            request.state.role = token_payload.role
            request.state.user_metadata = token_payload.user_metadata

            logger.debug(f"Auth middleware - User {token_payload.sub} accessing {path}")

        except Exception as e:
            logger.warning(f"Authentication error for {path}: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Process request
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.debug(f"{request.method} {path} - {response.status_code} ({process_time:.3f}s)")

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests and responses.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Callable:
        """Log request and response."""
        request_id = request.headers.get("X-Request-ID", "")

        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"- Client: {request.client.host if request.client else 'unknown'}"
        )

        response = await call_next(request)

        logger.info(
            f"[{request_id}] Response: {response.status_code}"
        )

        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle and log errors.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Callable:
        """Handle errors in requests."""
        try:
            response = await call_next(request)

            # Log errors (5xx)
            if 500 <= response.status_code < 600:
                logger.error(
                    f"Server error: {request.method} {request.url.path} - "
                    f"Status: {response.status_code}"
                )

            return response

        except Exception as exc:
            logger.exception(f"Unhandled exception: {str(exc)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Basic rate limiting middleware (for demonstration).

    For production, use a proper rate limiting library like slowapi.
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}  # {ip: [(timestamp, count)]}

    async def dispatch(self, request: Request, call_next: Callable) -> Callable:
        """Apply rate limiting."""
        # For production, integrate with Redis or similar
        # This is a simple in-memory implementation

        client_ip = request.client.host if request.client else "unknown"

        # Check rate limit (simplified)
        current_time = time.time()

        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Clean old requests (older than 1 minute)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < 60
        ]

        # Check if limit exceeded
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
            )

        # Add current request
        self.requests[client_ip].append(current_time)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.requests[client_ip])
        )

        return response

