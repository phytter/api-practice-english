from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.core.common.application.dto import MongoObjectId

class DialogueLine(BaseModel):
    character: Optional[str] = ''
    text: str
    start_time: float
    end_time: float

class DialogueMovie(BaseModel): 
    imdb_id: str
    title: str
    language: str = "en"

class DialogueIn(BaseModel):
    movie: Optional[DialogueMovie] = None
    difficulty_level: int
    duration_seconds: float 
    lines: List[DialogueLine]

class DialogueOut(DialogueIn):
    id: Optional[MongoObjectId] = Field(alias="_id", default=None)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class DialoguePracticeHistoryIn(BaseModel):
    dialogue_id: str
    user_id: str
    pronunciation_score: float
    fluency_score: float
    completed_at: datetime
    practice_duration_seconds: float
    character_played: Optional[str] = ''
    xp_earned: Optional[int] = 0

class DialoguePracticeHistoryOut(DialoguePracticeHistoryIn):
    id: Optional[MongoObjectId] = Field(alias="_id", default=None)
    dialogue: Optional[DialogueOut] = None 

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class PracticeResult(BaseModel):
    pronunciation_score: float
    fluency_score: float
    transcribed_text: str
    suggestions: List[dict]
    word_timings: List[dict]
    xp_earned: int = 0
