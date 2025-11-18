"""
Tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from web_app import app


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    """Get authentication token for testing"""
    # Login with default admin user
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@autojobapplier.com",
            "password": "Admin123!"
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_register_user(client):
    """Test user registration"""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_user(client):
    """Test that duplicate registration fails"""
    # First registration
    client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "TestPassword123!",
        }
    )

    # Duplicate should fail
    response = client.post(
        "/api/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "TestPassword123!",
        }
    )
    assert response.status_code == 400


def test_login(client):
    """Test user login"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@autojobapplier.com",
            "password": "Admin123!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_login_wrong_password(client):
    """Test login with wrong password"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@autojobapplier.com",
            "password": "WrongPassword"
        }
    )
    assert response.status_code == 401


def test_get_current_user(client, auth_headers):
    """Test getting current user info"""
    response = client.get(
        "/api/auth/me",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@autojobapplier.com"


def test_protected_endpoint_without_auth(client):
    """Test that protected endpoints require authentication"""
    response = client.get("/api/config")
    assert response.status_code == 403  # Forbidden without auth


def test_protected_endpoint_with_auth(client, auth_headers):
    """Test protected endpoint with authentication"""
    response = client.get(
        "/api/config",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_titles" in data
    assert "locations" in data


def test_get_statistics(client, auth_headers):
    """Test getting application statistics"""
    response = client.get(
        "/api/statistics",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    # Should have statistics structure
    assert isinstance(data, dict)


def test_get_applications(client, auth_headers):
    """Test getting applications list"""
    response = client.get(
        "/api/applications",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_invalid_token(client):
    """Test that invalid tokens are rejected"""
    response = client.get(
        "/api/config",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


def test_job_search_validation(client, auth_headers):
    """Test job search input validation"""
    # Missing required fields
    response = client.post(
        "/api/search",
        json={},
        headers=auth_headers
    )
    assert response.status_code == 422  # Validation error

    # Invalid platform
    response = client.post(
        "/api/search",
        json={
            "job_titles": ["Software Engineer"],
            "locations": ["Remote"],
            "platforms": ["invalid_platform"]
        },
        headers=auth_headers
    )
    assert response.status_code == 422


def test_application_config_validation(client, auth_headers):
    """Test application config validation"""
    # Invalid max_applications (too low)
    response = client.post(
        "/api/apply",
        json={
            "auto_submit": False,
            "max_applications": 0,  # Invalid
            "application_delay": 30
        },
        headers=auth_headers
    )
    assert response.status_code == 422

    # Invalid delay (too low)
    response = client.post(
        "/api/apply",
        json={
            "auto_submit": False,
            "max_applications": 20,
            "application_delay": 1  # Invalid (must be >= 5)
        },
        headers=auth_headers
    )
    assert response.status_code == 422
