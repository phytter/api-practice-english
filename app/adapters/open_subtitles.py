from typing import List
from app.integration.http_client import HttpClient
from app.core.config import settings
from app.core.ports import SubtitleMovies
from app.model import MovieSearchOut

class OpenSubTitles(SubtitleMovies):
    api_key: str = settings.OPENSUBTITLES_API_KEY
    base_url: str = settings.OPENSUBTITLES_API_URL

    @classmethod
    async def search_movies(cls, query: str) -> List[MovieSearchOut]:
        headers = {
            "Api-Key": cls.api_key,
            "Content-Type": "application/json"
        }

        async with HttpClient.session.get(
            f"{cls.base_url}/features",
            headers=headers,
            params={
                "query": query,
                "type": "movie"
            }
        ) as response:
            if response.status == 200:
                data = await response.json()
                return [
                    MovieSearchOut(
                        title=item.get("attributes", {}).get("title"),
                        year=int(item.get("attributes", {}).get("year") or 0),
                        imdb_id=item.get("attributes", {}).get("imdb_id"),
                        feature_type=item.get("attributes", {}).get("feature_type", ""),
                        img_url=item.get("attributes", {}).get("img_url"),
                    )                    
                    for item in data.get("data", [])
                ]
            else:
                error_message = await response.text()
                raise Exception(f"Failed to search movies: {error_message}")

