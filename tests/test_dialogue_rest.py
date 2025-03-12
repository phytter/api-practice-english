import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.http.rest.v1 import dialogue_v1
from app.integration.mongo import Mongo

BASE_URL = dialogue_v1.prefix
MOVIE_IMDB_ID = "123"
pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("wipe_data")]

@pytest_asyncio.fixture
async def wipe_data():
    await Mongo.dialogues.delete_many({})

def mock_dialogue():
    return {
      "movie": {
          "imdb_id": MOVIE_IMDB_ID,
          "title": "The Movie",
          "language": "en"
      },
      "difficulty_level": 2,
      "lines": [{ "character": "", "text": "", "start_time": 10, "end_time": 20 }],
      "duration_seconds": 10
    }
  
async def test_search_dialogues_empty_results(client: AsyncClient):

    res = await client.get(BASE_URL)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 0

async def test_search_dialogues(client: AsyncClient):

    dilogue_db = mock_dialogue()
    await Mongo.dialogues.insert_one(dilogue_db)

    res = await client.get(BASE_URL)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1
    assert json_data[0]['movie']['title'] == dilogue_db['movie']['title']

async def test_search_dialogues_with_query(client: AsyncClient):

    dilogue_db = mock_dialogue()
    await Mongo.dialogues.insert_one(dilogue_db)

    res = await client.get(f"{BASE_URL}?search=not_included")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 0

    res = await client.get(f"{BASE_URL}?search={dilogue_db['movie']['title']}")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1
    assert json_data[0]['movie']['title'] == dilogue_db['movie']['title']

async def test_search_dialogues_with_imdb(client: AsyncClient):

    dilogue_db = mock_dialogue()
    await Mongo.dialogues.insert_one(dilogue_db)

    res = await client.get(f"{BASE_URL}?imdb_id=not_included")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 0

    res = await client.get(f"{BASE_URL}?imdb_id={MOVIE_IMDB_ID}")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1
    assert json_data[0]['movie']['imdb_id'] == MOVIE_IMDB_ID


async def test_search_dialogues_with_pagination(client: AsyncClient):

    await Mongo.dialogues.insert_one(mock_dialogue())
    await Mongo.dialogues.insert_one(mock_dialogue())

    res = await client.get(f"{BASE_URL}?limit=1&skip=0")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1

    res = await client.get(f"{BASE_URL}?limit=2&skip=0")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 2


    res = await client.get(f"{BASE_URL}?limit=2&skip=1")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1


    res = await client.get(f"{BASE_URL}?limit=2&skip=2")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 0