"""
Tests for authentication module
"""

import pytest
from src.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    verify_token,
    UserStore,
)


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


def test_user_store_create_user():
    """Test user creation in UserStore"""
    store = UserStore()

    # Create a new user
    user = store.create_user(
        email="newuser@example.com",
        password="Password123!",
        full_name="New User"
    )

    assert user["email"] == "newuser@example.com"
    assert user["full_name"] == "New User"
    assert "hashed_password" in user
    assert user["is_active"] is True


def test_user_store_duplicate_email():
    """Test that duplicate emails are rejected"""
    store = UserStore()

    # First user should succeed
    store.create_user(
        email="duplicate@example.com",
        password="Password123!"
    )

    # Duplicate should fail
    with pytest.raises(ValueError, match="User already exists"):
        store.create_user(
            email="duplicate@example.com",
            password="Password123!"
        )


def test_user_store_authenticate():
    """Test user authentication"""
    store = UserStore()

    # Create a user
    password = "Password123!"
    store.create_user(
        email="auth@example.com",
        password=password
    )

    # Should authenticate with correct password
    user = store.authenticate_user("auth@example.com", password)
    assert user is not None
    assert user["email"] == "auth@example.com"

    # Should fail with wrong password
    user = store.authenticate_user("auth@example.com", "WrongPassword")
    assert user is None

    # Should fail with non-existent user
    user = store.authenticate_user("nonexistent@example.com", password)
    assert user is None


def test_default_admin_user():
    """Test that default admin user is created"""
    store = UserStore()

    # Default admin should exist
    admin = store.get_user_by_email("admin@autojobapplier.com")
    assert admin is not None
    assert admin["full_name"] == "Admin User"

    # Should be able to authenticate
    user = store.authenticate_user("admin@autojobapplier.com", "Admin123!")
    assert user is not None
