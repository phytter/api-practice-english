from .base import BaseModel, EmailStr, Field, Optional, List, MongoObjectId
from datetime import datetime

class Achievement(BaseModel):
    id: str
    name: str
    description: str
    earned_at: datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str
    picture: Optional[str] = None
    google_id: str = ''
    achievements: List[Achievement] = []
    created_at: datetime
    last_login: datetime

class UserIn(UserBase):
    pass

class UserOut(UserBase):
    id: MongoObjectId = Field(default_factory=MongoObjectId, alias="_id")


class UserUpdate(BaseModel):
    name: Optional[str] = None
    picture: Optional[str] = None
