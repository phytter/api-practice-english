from app.core.config import settings
from fastapi import APIRouter, Depends
from app.business import MovieBusiness, AuthBusiness
from typing import List, Dict, Optional
from app.core.movies.application.dto.movie_dto import MovieSearchOut, MovieOut


movie_v1 = APIRouter(
    prefix=f"{settings.API_V1_STR}/movies",
    tags=["movie"],
    dependencies=[Depends(AuthBusiness.validate_auth)]
)

@movie_v1.get(
    "/search",
    response_model=List[MovieSearchOut],
    status_code=200,
)
async def search_movies(
    search: str,
) -> List[MovieSearchOut]:
    return await MovieBusiness.search_movies(search)

@movie_v1.post(
    "/{imdb_id}/process",
    response_model=Dict,
    status_code=200,
)
async def process_movie_dialogues(
    imdb_id: str,
    language: str = "en",
) -> Dict:
    return await MovieBusiness.process_movie_dialogues(imdb_id, language)

@movie_v1.get(
    "/processed",
    response_model=List[MovieOut],
    status_code=200,
)
async def search_processed_movies(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[MovieOut]:
    return await MovieBusiness.search_processed_movies(search, skip, limit)
