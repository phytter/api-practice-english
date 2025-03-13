import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.http.rest.v1 import dialogue_v1
from app.integration.mongo import Mongo
from app.model import ObjectId

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

    dialogue_db = mock_dialogue()
    await Mongo.dialogues.insert_one(dialogue_db)

    res = await client.get(BASE_URL)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1
    assert json_data[0]['movie']['title'] == dialogue_db['movie']['title']

async def test_search_dialogues_with_query(client: AsyncClient):

    dialogue_db = mock_dialogue()
    await Mongo.dialogues.insert_one(dialogue_db)

    res = await client.get(f"{BASE_URL}?search=not_included")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 0

    res = await client.get(f"{BASE_URL}?search={dialogue_db['movie']['title']}")

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1
    assert json_data[0]['movie']['title'] == dialogue_db['movie']['title']

async def test_search_dialogues_with_imdb(client: AsyncClient):

    dialogue_db = mock_dialogue()
    await Mongo.dialogues.insert_one(dialogue_db)

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

async def test_get_dialogue(client: AsyncClient):

    dialogue_db = mock_dialogue()
    result = await Mongo.dialogues.insert_one(dialogue_db)
    dialogue_id = result.inserted_id

    res = await client.get(f"{BASE_URL}/{dialogue_id}")

    json_data = res.json()

    assert res.status_code == 200
    assert json_data['movie']['imdb_id'] == MOVIE_IMDB_ID
    assert json_data['_id'] == str(dialogue_id)

    non_existent_id = ObjectId()
    res = await client.get(f"{BASE_URL}/{non_existent_id}")

    json_data = res.json()

    assert res.status_code == 404
    assert json_data['detail'] == "Dialogue not found"