"""
Tests for user management API endpoints
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from web_app import app
from src.auth import create_user, authenticate_user, create_access_token
from src.user_service import user_service


# Create test client
client = TestClient(app)


@pytest.fixture
def admin_headers():
    """Get admin authentication headers"""
    # Login as admin
    admin = authenticate_user("admin@autojobapplier.com", "Admin123!")
    token = create_access_token(data={"sub": admin["email"], "user_id": admin["id"]})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def regular_user():
    """Create a regular user for testing"""
    email = f"testuser-{uuid.uuid4()}@example.com"
    user = create_user(
        email=email,
        password="TestPass123!",
        full_name="Test User"
    )
    return user


@pytest.fixture
def regular_user_headers(regular_user):
    """Get regular user authentication headers"""
    token = create_access_token(data={"sub": regular_user["email"], "user_id": regular_user["id"]})
    return {"Authorization": f"Bearer {token}"}


def test_get_my_profile(regular_user_headers):
    """Test getting current user's profile"""
    response = client.get("/api/users/me", headers=regular_user_headers)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "full_name" in data
    assert "is_active" in data
    assert "is_admin" in data
    assert data["is_active"] is True


def test_get_my_profile_unauthorized():
    """Test that accessing profile without auth fails"""
    response = client.get("/api/users/me")
    assert response.status_code == 403


def test_list_users_as_admin(admin_headers):
    """Test listing users as admin"""
    response = client.get("/api/users", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Check that admin user is in the list
    admin_emails = [u["email"] for u in data]
    assert "admin@autojobapplier.com" in admin_emails


def test_list_users_as_regular_user(regular_user_headers):
    """Test that regular users cannot list all users"""
    response = client.get("/api/users", headers=regular_user_headers)
    assert response.status_code == 403


def test_get_user_by_id_own_profile(regular_user, regular_user_headers):
    """Test getting own user profile by ID"""
    response = client.get(f"/api/users/{regular_user['id']}", headers=regular_user_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == regular_user["id"]
    assert data["email"] == regular_user["email"]


def test_get_user_by_id_other_user(regular_user_headers):
    """Test that regular users cannot access other users' profiles"""
    # Try to access admin user (id=1)
    response = client.get("/api/users/1", headers=regular_user_headers)
    assert response.status_code == 403


def test_get_user_by_id_as_admin(admin_headers, regular_user):
    """Test that admin can access any user's profile"""
    response = client.get(f"/api/users/{regular_user['id']}", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == regular_user["id"]
    assert data["email"] == regular_user["email"]


def test_update_own_profile(regular_user, regular_user_headers):
    """Test updating own profile"""
    update_data = {
        "full_name": "Updated Name"
    }

    response = client.put(
        f"/api/users/{regular_user['id']}",
        json=update_data,
        headers=regular_user_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"


def test_update_own_profile_cannot_change_admin_status(regular_user, regular_user_headers):
    """Test that regular users cannot change their admin status"""
    update_data = {
        "is_admin": True
    }

    response = client.put(
        f"/api/users/{regular_user['id']}",
        json=update_data,
        headers=regular_user_headers
    )

    assert response.status_code == 403


def test_update_other_user_as_regular_user(regular_user_headers):
    """Test that regular users cannot update other users"""
    update_data = {
        "full_name": "Hacked Name"
    }

    response = client.put(
        "/api/users/1",
        json=update_data,
        headers=regular_user_headers
    )

    assert response.status_code == 403


def test_update_user_as_admin(admin_headers, regular_user):
    """Test that admin can update any user"""
    update_data = {
        "full_name": "Admin Updated Name",
        "is_admin": True
    }

    response = client.put(
        f"/api/users/{regular_user['id']}",
        json=update_data,
        headers=admin_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Admin Updated Name"
    assert data["is_admin"] is True


def test_delete_user_as_admin(admin_headers):
    """Test deleting user as admin"""
    # Create a user to delete
    email = f"todelete-{uuid.uuid4()}@example.com"
    user = create_user(email=email, password="TestPass123!")

    response = client.delete(f"/api/users/{user['id']}", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify user is deactivated
    deleted_user = user_service.get_user_by_id(user["id"])
    assert deleted_user.is_active is False


def test_delete_user_as_regular_user(regular_user_headers):
    """Test that regular users cannot delete users"""
    # Create a user to attempt deletion
    email = f"todelete-{uuid.uuid4()}@example.com"
    user = create_user(email=email, password="TestPass123!")

    response = client.delete(f"/api/users/{user['id']}", headers=regular_user_headers)
    assert response.status_code == 403


def test_admin_cannot_delete_self(admin_headers):
    """Test that admin cannot delete their own account"""
    # Get admin user id (should be 1)
    response = client.get("/api/users/me", headers=admin_headers)
    admin_id = response.json()["id"]

    response = client.delete(f"/api/users/{admin_id}", headers=admin_headers)
    assert response.status_code == 400


def test_change_password_success(regular_user_headers):
    """Test successful password change"""
    password_data = {
        "current_password": "TestPass123!",
        "new_password": "NewPass456!"
    }

    response = client.post(
        "/api/users/change-password",
        json=password_data,
        headers=regular_user_headers
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_change_password_wrong_current_password(regular_user_headers):
    """Test password change with wrong current password"""
    password_data = {
        "current_password": "WrongPassword123!",
        "new_password": "NewPass456!"
    }

    response = client.post(
        "/api/users/change-password",
        json=password_data,
        headers=regular_user_headers
    )

    assert response.status_code == 400


def test_change_password_weak_new_password(regular_user_headers):
    """Test password change with weak new password"""
    password_data = {
        "current_password": "TestPass123!",
        "new_password": "weak"
    }

    response = client.post(
        "/api/users/change-password",
        json=password_data,
        headers=regular_user_headers
    )

    assert response.status_code == 422  # Validation error


def test_change_password_same_as_current(regular_user_headers):
    """Test password change with same password as current"""
    password_data = {
        "current_password": "TestPass123!",
        "new_password": "TestPass123!"
    }

    response = client.post(
        "/api/users/change-password",
        json=password_data,
        headers=regular_user_headers
    )

    assert response.status_code == 400


def test_change_password_unauthorized():
    """Test that changing password without auth fails"""
    password_data = {
        "current_password": "TestPass123!",
        "new_password": "NewPass456!"
    }

    response = client.post("/api/users/change-password", json=password_data)
    assert response.status_code == 403
