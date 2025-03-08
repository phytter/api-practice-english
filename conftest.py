import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
from aioresponses import aioresponses
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

    