"""
Tests for authentication module
"""

import pytest
from src.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    verify_token,
    authenticate_user,
    create_user,
)
from src.user_service import user_service


def test_password_hashing():
    """Test password hashing and verification"""
    password = "TestPassword123!"
    hashed = get_password_hash(password)

    # Should not be equal to plain password
    assert hashed != password

    # Should verify correctly
    assert verify_password(password, hashed) is True

    # Should fail with wrong password
    assert verify_password("WrongPassword", hashed) is False


def test_create_access_token():
    """Test JWT token creation"""
    data = {"sub": "test@example.com", "user_id": 1}
    token = create_access_token(data)

    # Token should be a string
    assert isinstance(token, str)

    # Token should have content
    assert len(token) > 0


def test_verify_token():
    """Test JWT token verification"""
    data = {"sub": "test@example.com", "user_id": 1}
    token = create_access_token(data)

    # Should decode successfully
    token_data = verify_token(token)

    assert token_data.email == "test@example.com"
    assert token_data.user_id == 1


def test_verify_invalid_token():
    """Test that invalid tokens are rejected"""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        verify_token("invalid_token")

    assert exc_info.value.status_code == 401


def test_user_service_create_user():
    """Test user creation with database"""
    import uuid
    email = f"newuser-{uuid.uuid4()}@example.com"

    # Create a new user
    user = create_user(
        email=email,
        password="Password123!",
        full_name="New User"
    )

    assert user["email"] == email
    assert user["full_name"] == "New User"
    assert user["is_active"] is True


def test_user_service_duplicate_email():
    """Test that duplicate emails are rejected"""
    import uuid
    email = f"duplicate-{uuid.uuid4()}@example.com"

    # First user should succeed
    create_user(
        email=email,
        password="Password123!"
    )

    # Duplicate should fail
    with pytest.raises(ValueError, match="User already exists"):
        create_user(
            email=email,
            password="Password123!"
        )


def test_user_service_authenticate():
    """Test user authentication"""
    import uuid
    email = f"auth-{uuid.uuid4()}@example.com"
    password = "Password123!"

    # Create a user
    create_user(
        email=email,
        password=password
    )

    # Should authenticate with correct password
    user = authenticate_user(email, password)
    assert user is not None
    assert user["email"] == email

    # Should fail with wrong password
    user = authenticate_user(email, "WrongPassword")
    assert user is None

    # Should fail with non-existent user
    user = authenticate_user("nonexistent@example.com", password)
    assert user is None


def test_default_admin_user():
    """Test that default admin user exists"""
    # Default admin should exist and authenticate
    user = authenticate_user("admin@autojobapplier.com", "Admin123!")
    assert user is not None
    assert user["email"] == "admin@autojobapplier.com"
