import pytest
from httpx import AsyncClient
from unittest.mock import patch
from app.core.common.application.dto import GoogleLoginData
from app.http.rest.v1 import auth_v1
import pytest_asyncio
from datetime import datetime, timezone

BASE_URL = auth_v1.prefix
TEST_USER_EMAIL = "test@example.com"
pytestmark = [
    pytest.mark.asyncio
]

@pytest.fixture
def google_login_data():
    return GoogleLoginData(token="test_token")

@pytest.fixture
def mock_google_user():
    return {
        "email": TEST_USER_EMAIL,
        "name": "Test User",
        "picture": "http://example.com/picture.jpg",
        "sub": "1234567890",
        "iss": "accounts.google.com"
    }

@pytest.fixture
def mock_db_user():
    return {
        "email": TEST_USER_EMAIL,
        "name": "Test User",
        "picture": "http://example.com/picture.jpg",
        "google_id": "1234567890",
        "achievements": [],
        "created_at": datetime.now(timezone.utc),
        "last_login": datetime.now(timezone.utc)
    }

@patch("google.oauth2.id_token.verify_oauth2_token")
async def test_google_login_success_new_user(
    mock_verify,
    client: AsyncClient,
    google_login_data,
    mock_google_user
):
    mock_verify.return_value = mock_google_user

    response = await client.post(
        f"{BASE_URL}/google-login",
        json=google_login_data.model_dump()
    )

    assert response.status_code == 200
    result = response.json()
    
    assert "access_token" in result
    assert result["token_type"] == "bearer"
    
    assert result["user"]["email"] == TEST_USER_EMAIL
    
@patch("google.oauth2.id_token.verify_oauth2_token")
async def test_google_login_success_exist_user(
    mock_verify,
    client: AsyncClient,
    google_login_data,
    mock_google_user,
    mock_db_user
):
    from app.integration import Mongo

    mock_db_user['last_login'] =  mock_db_user['created_at']

    await Mongo.users.insert_one(mock_db_user)
    mock_verify.return_value = mock_google_user

    response = await client.post(
        f"{BASE_URL}/google-login",
        json=google_login_data.model_dump()
    )

    assert response.status_code == 200
    result = response.json()
    
    assert "access_token" in result
    assert result["token_type"] == "bearer"
    
    assert result["user"]["email"] == TEST_USER_EMAIL
    assert result["user"]["last_login"] != result["user"]["created_at"]

async def test_dev_login_success_new_user(client: AsyncClient):
    from app.core.config import settings
    with patch.object(settings, "APP_DEBUG", True):
        response = await client.post(
            f"{BASE_URL}/dev-login",
            json={"email": "dev@local.com", "name": "Dev User"},
        )

    assert response.status_code == 200
    result = response.json()
    assert "access_token" in result
    assert result["token_type"] == "bearer"
    assert result["user"]["email"] == "dev@local.com"
    assert result["user"]["name"] == "Dev User"

async def test_dev_login_success_existing_user(client: AsyncClient):
    from app.core.config import settings
    with patch.object(settings, "APP_DEBUG", True):
        await client.post(
            f"{BASE_URL}/dev-login",
            json={"email": "dev@local.com", "name": "Dev User"},
        )
        response = await client.post(
            f"{BASE_URL}/dev-login",
            json={"email": "dev@local.com", "name": "Dev User"},
        )

    assert response.status_code == 200
    result = response.json()
    assert result["user"]["email"] == "dev@local.com"
    assert result["user"]["last_login"] != result["user"]["created_at"]

async def test_dev_login_forbidden_when_not_debug(client: AsyncClient):
    from app.core.config import settings
    with patch.object(settings, "APP_DEBUG", False):
        response = await client.post(
            f"{BASE_URL}/dev-login",
            json={"email": "dev@local.com", "name": "Dev User"},
        )

    assert response.status_code == 403