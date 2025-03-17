from app.core.config import settings
from fastapi import APIRouter, File, Form, UploadFile
from app.business import DialogueBusiness
from typing import List, Optional
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

@dialogue_v1.get(
    "/{dialogue_id}",
    response_model=DialogueOut,
    status_code=200,
)
async def show_dialogue(
    dialogue_id: str,
) -> DialogueOut:
    return await DialogueBusiness.show_dialogue(dialogue_id)

@dialogue_v1.post(
    "/{dialogue_id}/practice",
    status_code=200,
)
async def practice_dialogue(
    dialogue_id: str,
    audio: UploadFile = File(...), 
) -> None:
    audio_data = await audio.read()
    return await DialogueBusiness.proccess_practice_dialogue(dialogue_id, audio_data)
