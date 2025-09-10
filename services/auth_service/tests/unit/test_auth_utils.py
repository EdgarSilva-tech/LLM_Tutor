import pytest
from unittest.mock import patch, MagicMock
from datetime import timedelta
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import HTTPException

# Import functions from the auth_utils module using absolute paths
from services.auth_service.auth_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    authenticate_user,
    get_current_user,
    AUTH_SECRET,
    ALGORITHM,
)
from services.auth_service.data_models import UserInDB, TokenData

# --- Tests for Password Functions ---


def test_get_password_hash():
    """Test that a password gets hashed correctly."""
    password = "testpassword123"
    hashed_password = get_password_hash(password)
    assert hashed_password != password
    assert isinstance(hashed_password, str)


def test_verify_password():
    """Test that password verification works for correct and incorrect passwords."""
    password = "testpassword123"
    hashed_password = get_password_hash(password)
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrongpassword", hashed_password) is False

# --- Test for JWT Token Creation ---


def test_create_access_token():
    """Test the creation of a JWT access token."""
    data = {"sub": "testuser"}
    token = create_access_token(data)
    decoded_payload = jwt.decode(token, AUTH_SECRET, algorithms=[ALGORITHM])
    assert decoded_payload["sub"] == "testuser"
    assert "exp" in decoded_payload


def test_create_access_token_with_delta():
    """Test token creation with a specific expiry delta."""
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=30)
    token = create_access_token(data, expires_delta=expires_delta)
    decoded_payload = jwt.decode(token, AUTH_SECRET, algorithms=[ALGORITHM])
    assert decoded_payload["sub"] == "testuser"
    # Check if 'exp' (expiration time) is roughly 30 minutes from now
    assert "exp" in decoded_payload
    # Further checks could be done on the expiration time if needed

# --- Tests for User Authentication Logic ---


@patch('services.auth_service.auth_utils.get_user')
def test_authenticate_user_success(mock_get_user):
    """Test successful user authentication."""
    mock_user = UserInDB(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        disabled=False,
        hashed_password=get_password_hash("password123"),
    )
    mock_get_user.return_value = mock_user

    user = authenticate_user("testuser", "password123")
    assert user is not False
    assert user.username == "testuser"
    mock_get_user.assert_called_once_with("testuser")


@patch('services.auth_service.auth_utils.get_user')
def test_authenticate_user_wrong_password(mock_get_user):
    """Test authentication failure with the wrong password."""
    mock_user = UserInDB(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        disabled=False,
        hashed_password=get_password_hash("password123"),
    )
    mock_get_user.return_value = mock_user

    result = authenticate_user("testuser", "wrongpassword")
    assert result is False
    mock_get_user.assert_called_once_with("testuser")


@patch('services.auth_service.auth_utils.get_user')
def test_authenticate_user_not_found(mock_get_user):
    """Test authentication failure when the user does not exist."""
    mock_get_user.return_value = None

    result = authenticate_user("nonexistentuser", "password123")
    assert result is False
    mock_get_user.assert_called_once_with("nonexistentuser")

# --- Tests for Getting Current User from Token ---


@pytest.mark.asyncio
@patch('services.auth_service.auth_utils.get_user')
@patch('jwt.decode')
async def test_get_current_user_success(mock_jwt_decode, mock_get_user):
    """Test successfully getting a user from a valid token."""
    mock_payload = {"sub": "testuser"}
    mock_jwt_decode.return_value = mock_payload
    
    # FIX: Add the required 'hashed_password' field to the UserInDB instance.
    mock_user = UserInDB(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password="a-dummy-hashed-password"
    )
    mock_get_user.return_value = mock_user

    token = "valid.token.here"
    user = await get_current_user(token)

    assert user.username == "testuser"
    mock_jwt_decode.assert_called_once_with(token, AUTH_SECRET, algorithms=[ALGORITHM])
    mock_get_user.assert_called_once_with(username="testuser")


@pytest.mark.asyncio
@patch('jwt.decode')
async def test_get_current_user_invalid_token(mock_jwt_decode):
    """Test handling of an invalid token."""
    mock_jwt_decode.side_effect = InvalidTokenError

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user("invalid.token.here")

    assert excinfo.value.status_code == 401


@pytest.mark.asyncio
@patch('jwt.decode')
async def test_get_current_user_no_username(mock_jwt_decode):
    """Test handling of a token with no 'sub' (username) payload."""
    mock_jwt_decode.return_value = {"other_claim": "value"} # No 'sub'

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user("token.without.sub")

    assert excinfo.value.status_code == 401


@pytest.mark.asyncio
@patch('services.auth_service.auth_utils.get_user')
@patch('jwt.decode')
async def test_get_current_user_user_not_found(mock_jwt_decode, mock_get_user):
    """Test handling when the user from the token is not found in the DB."""
    mock_jwt_decode.return_value = {"sub": "nonexistentuser"}
    mock_get_user.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user("valid.token.for.nonexistent.user")

    assert excinfo.value.status_code == 401
    mock_get_user.assert_called_once_with(username="nonexistentuser")
