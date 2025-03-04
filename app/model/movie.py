from .base import BaseModel, Field, PyObjectId
from datetime import datetime


class MovieBase(BaseModel):
    title: str
    year: int
    feature_type: str
    machine_translated: bool = False
    ai_translated: bool = False
    imdb_id: int

class MovieSearchOut(MovieBase):
    img_url: str
    ...

class MovieIn(MovieBase):
    all_movie_info: dict
    subtitle_id: str
    upload_date: datetime
    language: str = "en"
    id: PyObjectId = Field(alias="_id", default=None)
    content: str
