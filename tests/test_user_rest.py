import pytest
from httpx import AsyncClient
from app.http.rest.v1 import user_v1
import pytest_asyncio

BASE_URL = user_v1.prefix
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.usefixtures("wipe_auth")
]

@pytest_asyncio.fixture
async def wipe_auth():
    from app.integration import Mongo
    await Mongo.users.delete_many({})

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
    assert result["_id"] == user["_id"]