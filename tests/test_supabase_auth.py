"""
Tests for Supabase authentication system.
"""
import jwt
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.auth import SupabaseAuthManager, TokenPayload
from app.main import app

client = TestClient(app)


class TestSupabaseAuthManager:
    """Test Supabase authentication manager."""

    def setup_method(self):
        """Setup test fixtures."""
        self.auth_manager = SupabaseAuthManager()
        self.user_id = str(uuid4())
        self.email = "test@example.com"
        self.role = "customer"

    def create_token(self, **overrides):
        """Create a test JWT token."""
        now = datetime.utcnow()
        payload = {
            "aud": "authenticated",
            "sub": self.user_id,
            "email": self.email,
            "role": self.role,
            "user_metadata": {
                "username": "testuser"
            },
            "iss": settings.supabase_url,
            "iat": now,
            "exp": now + timedelta(hours=1),
        }
        payload.update(overrides)

        token = jwt.encode(
            payload,
            self.auth_manager.jwt_secret,
            algorithm="HS256"
        )
        return token

    def test_verify_valid_token(self):
        """Test verification of valid token."""
        token = self.create_token()
        token_payload = self.auth_manager.verify_token(token)

        assert str(token_payload.sub) == self.user_id
        assert token_payload.email == self.email
        assert token_payload.role == self.role

    def test_verify_token_with_bearer_prefix(self):
        """Test verification with Bearer prefix."""
        token = self.create_token()
        bearer_token = f"Bearer {token}"

        token_payload = self.auth_manager.verify_token(bearer_token)
        assert str(token_payload.sub) == self.user_id

    def test_verify_expired_token(self):
        """Test verification fails for expired token."""
        past = datetime.utcnow() - timedelta(hours=1)
        token = self.create_token(exp=past, iat=past - timedelta(hours=2))

        with pytest.raises(Exception):  # ExpiredSignatureError
            self.auth_manager.verify_token(token)

    def test_verify_invalid_signature(self):
        """Test verification fails with invalid signature."""
        token = self.create_token()
        # Corrupt token
        corrupted = token[:-10] + "0000000000"

        with pytest.raises(Exception):  # InvalidTokenError
            self.auth_manager.verify_token(corrupted)

    def test_extract_user_info(self):
        """Test extracting user info from token."""
        token = self.create_token()
        user_info = self.auth_manager.extract_user_info(token)

        assert str(user_info["user_id"]) == self.user_id
        assert user_info["email"] == self.email
        assert user_info["role"] == self.role

    def test_token_payload_from_dict(self):
        """Test TokenPayload creation from dictionary."""
        data = {
            "sub": self.user_id,
            "email": self.email,
            "role": "provider",
            "user_metadata": {"custom": "data"}
        }

        payload = TokenPayload.from_dict(data)
        assert str(payload.sub) == self.user_id
        assert payload.email == self.email
        assert payload.role == "provider"
        assert payload.user_metadata == {"custom": "data"}

    def test_decode_token_without_verification(self):
        """Test decoding token without verification."""
        token = self.create_token()
        decoded = SupabaseAuthManager.decode_token_without_verification(token)

        assert decoded["sub"] == self.user_id
        assert decoded["email"] == self.email


class TestAuthenticationDependencies:
    """Test authentication dependencies."""

    def setup_method(self):
        """Setup test fixtures."""
        self.auth_manager = SupabaseAuthManager()
        self.user_id = str(uuid4())
        self.email = "testuser@example.com"

    def create_token(self, role="customer", **overrides):
        """Create test token."""
        now = datetime.utcnow()
        payload = {
            "aud": "authenticated",
            "sub": self.user_id,
            "email": self.email,
            "role": role,
            "user_metadata": {},
            "iss": settings.supabase_url,
            "iat": now,
            "exp": now + timedelta(hours=1),
        }
        payload.update(overrides)

        return jwt.encode(
            payload,
            self.auth_manager.jwt_secret,
            algorithm="HS256"
        )

    def test_get_current_user_success(self):
        """Test get_current_user with valid token."""
        token = self.create_token()

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code in [200, 404]  # 404 if user not in DB

    def test_get_current_user_missing_token(self):
        """Test get_current_user without token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 403  # Forbidden (missing auth)

    def test_get_current_user_invalid_token(self):
        """Test get_current_user with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid"}
        )
        assert response.status_code == 403

    def test_get_customer_role(self):
        """Test get_current_customer with customer role."""
        token = self.create_token(role="customer")

        response = client.get(
            "/api/v1/auth/me/customer",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code in [200, 404]

    def test_get_provider_role(self):
        """Test get_current_provider with provider role."""
        token = self.create_token(role="provider")

        response = client.get(
            "/api/v1/auth/me/provider",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code in [200, 404]

    def test_get_admin_role(self):
        """Test get_current_admin with admin role."""
        token = self.create_token(role="admin")

        response = client.get(
            "/api/v1/auth/me/admin",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code in [200, 404]

    def test_customer_cannot_access_provider_endpoint(self):
        """Test customer cannot access provider-only endpoint."""
        token = self.create_token(role="customer")

        response = client.get(
            "/api/v1/auth/me/provider",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code in [403, 404]  # 403 if user in DB

    def test_provider_cannot_access_admin_endpoint(self):
        """Test provider cannot access admin-only endpoint."""
        token = self.create_token(role="provider")

        response = client.get(
            "/api/v1/auth/me/admin",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code in [403, 404]

    def test_admin_can_access_all_endpoints(self):
        """Test admin can access all role-restricted endpoints."""
        token = self.create_token(role="admin")

        # Try customer endpoint
        response1 = client.get(
            "/api/v1/auth/me/customer",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response1.status_code in [200, 404]

        # Try provider endpoint
        response2 = client.get(
            "/api/v1/auth/me/provider",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response2.status_code in [200, 404]

        # Try admin endpoint
        response3 = client.get(
            "/api/v1/auth/me/admin",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response3.status_code in [200, 404]

    def test_optional_user_with_token(self):
        """Test optional user with valid token."""
        token = self.create_token()

        response = client.get(
            "/api/v1/auth/optional-info",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "authenticated" in data

    def test_optional_user_without_token(self):
        """Test optional user without token."""
        response = client.get("/api/v1/auth/optional-info")

        assert response.status_code == 200
        data = response.json()
        assert data.get("authenticated") == False


class TestAuthorizationRoles:
    """Test role-based authorization."""

    def test_role_constants(self):
        """Test role constants."""
        from app.models import UserRole

        assert UserRole.CUSTOMER == "customer"
        assert UserRole.PROVIDER == "provider"
        assert UserRole.ADMIN == "admin"
        assert len(UserRole.ALL_ROLES) == 3

    def test_role_in_user_model(self):
        """Test role field in User model."""
        from app.models import User
        from uuid import uuid4

        user = User(
            id=uuid4(),
            email="test@example.com",
            username="testuser",
            role="provider"
        )

        assert user.role == "provider"


class TestUnprotectedRoutes:
    """Test unprotected routes work without auth."""

    def test_health_check_no_auth(self):
        """Test health endpoint without auth."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_root_no_auth(self):
        """Test root endpoint without auth."""
        response = client.get("/")
        assert response.status_code == 200

    def test_docs_no_auth(self):
        """Test docs endpoint without auth."""
        response = client.get("/docs")
        assert response.status_code in [200, 404]  # 404 if redirected

    def test_openapi_no_auth(self):
        """Test OpenAPI schema without auth."""
        response = client.get("/openapi.json")
        assert response.status_code in [200, 404]


class TestTokenExpiration:
    """Test token expiration handling."""

    def setup_method(self):
        """Setup test fixtures."""
        self.auth_manager = SupabaseAuthManager()
        self.user_id = str(uuid4())
        self.email = "test@example.com"

    def test_token_with_future_expiration(self):
        """Test token with future expiration."""
        now = datetime.utcnow()
        future = now + timedelta(hours=1)

        payload = {
            "aud": "authenticated",
            "sub": self.user_id,
            "email": self.email,
            "role": "customer",
            "exp": future,
            "iat": now,
        }

        token = jwt.encode(
            payload,
            self.auth_manager.jwt_secret,
            algorithm="HS256"
        )

        # Should not raise
        token_payload = self.auth_manager.verify_token(token)
        assert str(token_payload.sub) == self.user_id

    def test_token_with_past_expiration(self):
        """Test token with past expiration."""
        now = datetime.utcnow()
        past = now - timedelta(hours=1)

        payload = {
            "aud": "authenticated",
            "sub": self.user_id,
            "email": self.email,
            "role": "customer",
            "exp": past,
            "iat": past - timedelta(hours=2),
        }

        token = jwt.encode(
            payload,
            self.auth_manager.jwt_secret,
            algorithm="HS256"
        )

        # Should raise ExpiredSignatureError
        with pytest.raises(Exception):
            self.auth_manager.verify_token(token)

