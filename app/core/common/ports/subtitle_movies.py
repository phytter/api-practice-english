from abc import ABC, abstractmethod
from typing import List
from app.core.movies.application.dto.movie_dto import MovieSearchOut

class SubtitleMovies(ABC):

    @abstractmethod
    async def search_movies(cls, query: str) -> List[MovieSearchOut]:
        pass
