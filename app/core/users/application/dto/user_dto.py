from app.core.common.application.dto import BaseModel, EmailStr, Field, Optional, List, MongoObjectId
from datetime import datetime

class Achievement(BaseModel):
    id: str
    name: str
    description: str
    earned_at: datetime

class UserProgress(BaseModel):
    total_practice_time_seconds: int = 0
    total_dialogues: int = 0
    average_pronunciation_score: float = 0.0
    average_fluency_score: float = 0.0
    level: int = 1
    xp_points: int = 0

class UserIn(BaseModel):
    email: EmailStr
    name: str
    picture: Optional[str] = ''
    google_id: str = ''
    achievements: List[Achievement] = []
    created_at: datetime
    last_login: datetime
    progress: Optional[UserProgress] = UserProgress(
        total_practice_time_seconds=0,
        average_fluency_score=0,
        average_pronunciation_score=0,
        level=0,
        total_dialogues=0,
        xp_points=0
    )

class UserOut(UserIn):
    id: MongoObjectId = Field(default_factory=MongoObjectId, alias="_id")

class UserUpdate(BaseModel):
    name: Optional[str] = None
    picture: Optional[str] = None
