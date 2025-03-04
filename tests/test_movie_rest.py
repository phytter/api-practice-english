import pytest
from app.http.rest.v1 import movie_v1
from httpx import AsyncClient
import re


BASE_URL = movie_v1.prefix
pytestmark = [pytest.mark.asyncio]

def mockOpenSubtitlesMovie():
    return {
        "attributes": {
            "title": "The Matrix",
            "year": 1999,
            "imdb_id": 123,
            "feature_type": "movie",
            "img_url": "asdsaas"
        }
    }

async def test_search_movies_open_subtitles(client: AsyncClient, responses):
    mockedOpenSubtitlesMovie = mockOpenSubtitlesMovie()
    responses.get(
      re.compile(r".*"),
      payload={
        "data": [mockedOpenSubtitlesMovie]
      }
    )
    res = await client.get(
        f"{BASE_URL}/search", 
        params={"query": "Matrix"}
    )

    json = res.json()

    assert res.status_code == 200
    assert len(json) == 1
    assert json[0].get('title') == mockedOpenSubtitlesMovie['attributes']['title']
    assert json[0].get("imdb_id") == mockedOpenSubtitlesMovie['attributes']['imdb_id']