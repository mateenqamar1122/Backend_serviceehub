"""
Sample tests for authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_new_user():
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email():
    """Test registration with duplicate email."""
    # First registration
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser1",
            "password": "TestPassword123!",
        }
    )

    # Second registration with same email
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser2",
            "password": "TestPassword123!",
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success():
    """Test successful login."""
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "logintest@example.com",
            "username": "loginuser",
            "password": "LoginPassword123!",
        }
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={
            "email": "logintest@example.com",
            "password": "LoginPassword123!",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_invalid_password():
    """Test login with invalid password."""
    # Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "invalidpw@example.com",
            "username": "invaliduser",
            "password": "CorrectPassword123!",
        }
    )

    # Login with wrong password
    response = client.post(
        "/api/v1/auth/login",
        data={
            "email": "invalidpw@example.com",
            "password": "WrongPassword123!",
        }
    )
    assert response.status_code == 401


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

