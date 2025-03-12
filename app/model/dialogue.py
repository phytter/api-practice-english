from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from .base import PyObjectId, MongoObjectId

class DialogueLine(BaseModel):
    character: Optional[str] = ''
    text: str
    start_time: float
    end_time: float

class DialogueMovie(BaseModel): 
    imdb_id: str
    title: str
    language: str = "en"

class Dialogue(BaseModel):
    movie: Optional[DialogueMovie] = None
    difficulty_level: int
    duration_seconds: float 
    lines: List[DialogueLine]
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class DialogueOut(Dialogue):
    id: Optional[MongoObjectId] = Field(alias="_id", default=None)

class DialogueProgress(BaseModel):
    id: Optional[MongoObjectId] = Field(alias="_id", default=None)
    dialogue_id: str
    user_id: str
    pronunciation_score: float
    fluency_score: float
    completed_at: datetime
    practice_duration_seconds: float
    character_played: Optional[str] = ''
    xp_earned: Optional[int] = 0
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class DialogueProgressOut(BaseModel):
    id: Optional[MongoObjectId] = Field(alias="_id", default=None)
    dialogue_id: str
    user_id: str
    dialogue: Optional[Dialogue] = None
    pronunciation_score: float
    fluency_score: float
    completed_at: datetime
    practice_duration_seconds: float
    character_played: Optional[str] = ''
    xp_earned: Optional[int] = 0

class DialoguePractice(BaseModel):
    dialogue_id: str
    character: str
    audio_chunk: bytes
    line_index: int

class PracticeResult(BaseModel):
    pronunciation_score: float
    fluency_score: float
    transcribed_text: str
    suggestions: List[dict]
    xp_earned: int
