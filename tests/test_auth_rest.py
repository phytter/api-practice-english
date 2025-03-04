import pytest
from httpx import AsyncClient
from unittest.mock import patch
from app.model import GoogleLoginData
from app.http.rest.v1 import auth_v1

BASE_URL = auth_v1.prefix
TEST_USER_EMAIL = "test@example.com"

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

@pytest.mark.asyncio
@patch("google.oauth2.id_token.verify_oauth2_token")
async def test_google_login_success(
    mock_verify,
    client: AsyncClient,
    google_login_data,
    mock_google_user
):
    mock_verify.return_value = mock_google_user

    response = await client.post(
        f"{BASE_URL}/google-login",
        json=google_login_data.dict()
    )

    assert response.status_code == 200
    result = response.json()
    
    assert "access_token" in result
    assert result["token_type"] == "bearer"
    
    assert result["user"]["email"] == TEST_USER_EMAIL
    