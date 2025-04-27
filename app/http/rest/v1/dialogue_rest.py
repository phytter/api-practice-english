from app.core.config import settings
from fastapi import APIRouter, File, UploadFile, Depends
from app.business import DialogueBusiness, AuthBusiness
from typing import List, Optional
from app.core.dialogues.application.dto.dialogue_dto import DialogueOut, PracticeResult, DialoguePracticeHistoryOut
from app.core.users.application.dto.user_dto import UserOut


dialogue_v1 = APIRouter(
    prefix=f"{settings.API_V1_STR}/dialogues",
    tags=["dialogue"],
    dependencies=[Depends(AuthBusiness.validate_auth)]
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
async def get_dialogue(
    dialogue_id: str,
) -> DialogueOut:
    return await DialogueBusiness.get_dialogue(dialogue_id)

@dialogue_v1.post(
    "/{dialogue_id}/practice",
    status_code=200,
    response_model=PracticeResult
)
async def practice_dialogue(
    dialogue_id: str,
    audio: UploadFile = File(...),
    user: UserOut = Depends(AuthBusiness.get_current_user) 
) -> None:
    audio_data = await audio.read()
    return await DialogueBusiness.proccess_practice_dialogue(dialogue_id, audio_data, user)

@dialogue_v1.get(
    "/practice/history",
    response_model=List[DialoguePracticeHistoryOut],
    status_code=200,
)
async def list_practice_history(
    filter_type: str = 'recent',
    skip: int = 0,
    limit: int = 20,
    user: UserOut = Depends(AuthBusiness.get_current_user)
) -> List[DialoguePracticeHistoryOut]:
    return await DialogueBusiness.list_practice_history(filter_type, skip, limit, user)