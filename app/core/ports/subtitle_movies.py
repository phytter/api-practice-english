from abc import ABC, abstractmethod
from typing import Dict, List
from app.model import MovieSearchOut

class SubtitleMovies(ABC):
    @classmethod
    async def search_movies(cls, query: str) -> List[MovieSearchOut]:
        pass
