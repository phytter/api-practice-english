import re
import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.http.rest.v1 import movie_v1
from app.integration.mongo import Mongo

BASE_URL = movie_v1.prefix
MOVIE_IMDB_ID = "123"
DOWNLOAD_LINK_FILE = "http://example.com/subtitle"
pytestmark = [pytest.mark.asyncio, pytest.mark.usefixtures("wipe_data")]

@pytest_asyncio.fixture
async def wipe_data():
    await Mongo.dialogues.delete_many({})
    await Mongo.movies_processed.delete_many({})

def mock_open_subtitles_movie():
    return {
        "attributes": {
            "title": "The Matrix",
            "year": 1999,
            "imdb_id": MOVIE_IMDB_ID,
            "feature_type": "movie",
            "img_url": "asdsaas"
        }
    }

def mock_get_subtitle_content ():
    return """
        00:02:19,723 --> 00:02:20,929
        Buzz lightyear mission log.

        2
        00:02:21,016 --> 00:02:23,974
        All signs point to this planet
        as the location of zurg's fortress,

        3
        00:02:24,061 --> 00:02:27,849
        but there seems to be no sign
        of intelligent life anywhere.

        4
        00:03:25,330 --> 00:03:27,742
        Come to me, my prey.

        5
        00:04:10,000 --> 00:04:13,743
        To infinity and beyond!

        6
        00:04:25,807 --> 00:04:28,594
        So, we meet again,
        buzz lightyear, for the last time.

        7
        00:04:28,685 --> 00:04:30,016
        Not today, zurg!

        8
        00:04:49,331 --> 00:04:51,572
        - No, no, no, no.
        - Oh, you almost had him.

        9
        00:04:51,708 --> 00:04:54,745
        - I'm never gonna defeat zurg!
        - Sure, you will, Rex.

        10
        00:04:54,836 --> 00:04:56,355
        In fact, you're a better buzz than I am.
    """

def mock_open_subtitles_subtitle():
    return {
        "attributes": {
            "files": [{"file_id": "123"}],
            "subtitle_id": "sub123",
            "feature_details": {
                "title": "Test Movie",
                "year": 2021,
                "feature_type": "movie"
            },
            "upload_date": "2021-01-01T00:00:00+00:00",
            "machine_translated": False,
            "ai_translated": False,
            "language": "en"
        },
        "ratings": 5
    }

def mock_movie_processed_db():
    return {
      "title": "The Matrix",
      "year": 1999,
      "imdb_id": MOVIE_IMDB_ID,
      "upload_date": "2021-01-01T00:00:00+00:00",
      "feature_type": "movie",
      "img_url": "asdsaas",
      "subtitle_id": "asdasdas",
      "machine_translated": False,
      "ai_translated": False,
      "content": "",
      "language": "en",
      "all_movie_info": {
          "files": [{"file_id": "321"}],
      },
    }

async def test_search_movies_open_subtitles(client: AsyncClient, responses, mock_auth_user_and_header):
    headers, _ = mock_auth_user_and_header
    mockedOpenSubtitlesMovie = mock_open_subtitles_movie()
    responses.get(
      re.compile(r".*/features"),
      payload={
        "data": [mockedOpenSubtitlesMovie]
      }
    )
    res = await client.get(
        f"{BASE_URL}/search", 
        params={"search": "Matrix"},
        headers=headers
    )

    json = res.json()

    assert res.status_code == 200
    assert len(json) == 1
    assert json[0].get('title') == mockedOpenSubtitlesMovie['attributes']['title']
    assert json[0].get("imdb_id") == mockedOpenSubtitlesMovie['attributes']['imdb_id']


async def test_process_movie_sub_empty_content(client: AsyncClient, responses, mock_auth_user_and_header):
    headers, _ = mock_auth_user_and_header
    responses.get(
        re.compile(r".*/subtitles"),
        payload={
            "data": [mock_open_subtitles_subtitle()]
        }
    )
    responses.post(
        re.compile(r".*/download"),
        payload={"link": DOWNLOAD_LINK_FILE}
    )
    responses.get(
        DOWNLOAD_LINK_FILE,
        body=""
    )

    res = await client.post(f"{BASE_URL}/{MOVIE_IMDB_ID}/process", headers=headers)

    json = res.json()

    assert res.status_code == 200
    assert json.get('dialogues_count') == 0

async def test_process_movie_with_no_cache(client: AsyncClient, responses, mock_auth_user_and_header):
    headers, _ = mock_auth_user_and_header
    responses.get(
        re.compile(r".*/subtitles"),
        payload={
            "data": [mock_open_subtitles_subtitle()]
        }
    )
    responses.post(
        re.compile(r".*/download"),
        payload={"link": DOWNLOAD_LINK_FILE}
    )
    responses.get(
        DOWNLOAD_LINK_FILE,
        body=mock_get_subtitle_content()
    )

    res = await client.post(f"{BASE_URL}/{MOVIE_IMDB_ID}/process", headers=headers)

    json = res.json()

    assert res.status_code == 200
    assert json.get('dialogues_count') == 1

async def test_process_movie_with_cache(client: AsyncClient, responses, mock_auth_user_and_header):
    headers, _ = mock_auth_user_and_header
    movie_processed_db = mock_movie_processed_db()
    movie_processed_db['content'] = ""
    await Mongo.movies_processed.insert_one(movie_processed_db)

    responses.get(
        re.compile(r".*/subtitles"),
        payload={
            "data": [mock_open_subtitles_subtitle()]
        }
    )
    responses.post(
        re.compile(r".*/download"),
        payload={"link": DOWNLOAD_LINK_FILE}
    )
    responses.get(
        DOWNLOAD_LINK_FILE,
        body=mock_get_subtitle_content()
    )

    res = await client.post(f"{BASE_URL}/{MOVIE_IMDB_ID}/process", headers=headers)

    json = res.json()

    assert res.status_code == 200
    assert json.get('dialogues_count') == 0

async def test_list_processed_movie(client: AsyncClient, mock_auth_user_and_header):
    headers, _ = mock_auth_user_and_header
    movie_processed_db = mock_movie_processed_db()
    await Mongo.movies_processed.insert_one(movie_processed_db)

    res = await client.get(f"{BASE_URL}/processed", headers=headers)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1
    assert json_data[0]['title'] == movie_processed_db['title']

async def test_search_processed_movie(client: AsyncClient, mock_auth_user_and_header):
    headers, _ = mock_auth_user_and_header
    movie_processed_db = mock_movie_processed_db()
    await Mongo.movies_processed.insert_one(movie_processed_db)

    res = await client.get(f"{BASE_URL}/processed?search={movie_processed_db['title']}", headers=headers)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1

    res = await client.get(f"{BASE_URL}/processed?search=not_included", headers=headers)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 0

async def test_search_processed_movie_with_pagination(client: AsyncClient, mock_auth_user_and_header):
    headers, _ = mock_auth_user_and_header
    await Mongo.movies_processed.insert_one(mock_movie_processed_db())
    await Mongo.movies_processed.insert_one(mock_movie_processed_db())

    res = await client.get(f"{BASE_URL}/processed?limit=1&skip=0", headers=headers)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1

    res = await client.get(f"{BASE_URL}/processed?limit=2&skip=0", headers=headers)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 2


    res = await client.get(f"{BASE_URL}/processed?limit=2&skip=1", headers=headers)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 1


    res = await client.get(f"{BASE_URL}/processed?limit=2&skip=2", headers=headers)

    json_data = res.json()

    assert res.status_code == 200
    assert len(json_data) == 0