from app.core.config import settings
from fastapi import APIRouter
from app.business import MovieBusiness
from typing import List, Dict
from app.model import MovieSearchOut


movie_v1 = APIRouter(
    prefix=f"{settings.API_V1_STR}/movies",
    tags=["movie"],
)

@movie_v1.get(
    "/search",
    response_model=List[MovieSearchOut],
    status_code=200,
)
async def search_movies(
    query: str,
) -> List[MovieSearchOut]:
    return await MovieBusiness.search_movies(query)