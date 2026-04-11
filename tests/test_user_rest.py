import pytest
from httpx import AsyncClient
from app.http.rest.v1 import user_v1
import pytest_asyncio

BASE_URL = user_v1.prefix
pytestmark = [
    pytest.mark.asyncio
]
async def test_user_profile(
    client: AsyncClient,
    mock_auth_user_and_header
):
    headers, user = mock_auth_user_and_header
    response = await client.get(
        f"{BASE_URL}/profile",
        headers=headers
    )

    assert response.status_code == 200
    result = response.json()
    
    assert result["email"] == user["email"]
    assert "_id" in result