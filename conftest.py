import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from aioresponses import aioresponses
from app.http.rest.v1 import auth_v1
import pytest_asyncio
import asyncio

import logging
import os

logger = logging.getLogger(__name__)
os.environ["ENV_FILE"] = ".env.test"

@pytest_asyncio.fixture(scope="session")
async def test_app():

    from app.main import app
    logger.debug(f"test_app session")
    async with LifespanManager(app) as manager:
        from app.integration import Mongo


        db_name = Mongo.db.name

        if db_name != "test":
            pytest.exit(f"O nome da base de dados é `{db_name}` porém só é permitido o nome `test` nos testes unitários")

        yield manager.app

@pytest_asyncio.fixture(scope="session")
async def client(test_app):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        yield client

@pytest.fixture
def responses():
    with aioresponses() as responses:
        yield responses

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(autouse=True)
async def clean_database():
    # Runs the cleanup AFTER the test finishes
    yield
    from app.integration import Mongo
    if Mongo.users is not None:
        print("\n[CLEANING DB] Deleting all test records...")
        await Mongo.users.delete_many({})
        await Mongo.movies_processed.delete_many({})
        await Mongo.dialogues.delete_many({})
        await Mongo.dialogue_practice_history.delete_many({})
        count = await Mongo.users.count_documents({})
        print(f"[CLEANING DB] Users left: {count}")
    
@pytest_asyncio.fixture
@patch("google.oauth2.id_token.verify_oauth2_token")
async def mock_user_google_auth(
    mock_verify,
    client: AsyncClient
):
    import uuid
    mock_verify.return_value = {
        "email": "test@example.com",
        "name": "Test User",
        "picture": "http://example.com/picture.jpg",
        "sub": str(uuid.uuid4()),
        "iss": "accounts.google.com"
    }

    response = await client.post(
        f"{auth_v1.prefix}/google-login",
        json={ "token": "faketoken" }
    )

    return response.json()

@pytest_asyncio.fixture
async def mock_auth_user_and_header(
    mock_user_google_auth
):
    return {"Authorization": f"Bearer {mock_user_google_auth['access_token']}"}, mock_user_google_auth['user']