from typing import List
from app.integration.connector import get_subtitle_movie_connector
from app.model import MovieSearchOut

class MovieBusiness:
    subtitle_movie = get_subtitle_movie_connector()
    @classmethod
    async def search_movies(cls, query: str) -> List[MovieSearchOut]:
        return await cls.subtitle_movie.search_movies(query)
