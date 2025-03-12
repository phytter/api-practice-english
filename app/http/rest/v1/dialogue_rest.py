from app.core.config import settings
from fastapi import APIRouter
from app.business import DialogueBusiness
from typing import List, Dict, Optional
from app.model import DialogueOut


dialogue_v1 = APIRouter(
    prefix=f"{settings.API_V1_STR}/dialogues",
    tags=["dialogue"],
)

@dialogue_v1.get(
    "",
    response_model=List[DialogueOut],
    status_code=200,
)
async def search_dialogues(
    search: Optional[str] = None,
    imdb_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[DialogueOut]:
    return await DialogueBusiness.search_dialogues(search, imdb_id, skip, limit)
