from typing import Any, Dict
from datetime import datetime
from app.core.common.domain.entity import Entity
from app.core.common.domain.value_objects import Uuid

class MovieEntity(Entity):
    def __init__(
        self,
        title: str,
        year: int,
        feature_type: str,
        imdb_id: str,
        subtitle_id: str,
        all_movie_info: Dict[str, Any],
        upload_date: datetime,
        content: str,
        language: str = "en",
        machine_translated: bool = False,
        ai_translated: bool = False,
        id: Uuid = None
    ):
        self.id = id
        self.title = title
        self.year = year
        self.feature_type = feature_type
        self.imdb_id = imdb_id
        self.subtitle_id = subtitle_id
        self.all_movie_info = all_movie_info
        self.upload_date = upload_date
        self.content = content
        self.language = language
        self.machine_translated = machine_translated
        self.ai_translated = ai_translated
        self._validate()

    def create(
        title: str,
        year: int,
        feature_type: str,
        imdb_id: str,
        subtitle_id: str,
        all_movie_info: Dict[str, Any],
        upload_date: datetime,
        content: str,
        language: str = "en",
        machine_translated: bool = False,
        ai_translated: bool = False,
        id: str = None
    ):
        return MovieEntity(
            title=title,
            year=year,
            feature_type=feature_type,
            imdb_id=imdb_id,
            subtitle_id=subtitle_id,
            all_movie_info=all_movie_info,
            upload_date=upload_date,
            content=content,
            language=language,
            machine_translated=machine_translated,
            ai_translated=ai_translated,
            id=Uuid(id)
        )
    
    def _validate(self) -> None:
        self._validate_imdb_id()
    
    def _validate_imdb_id(self) -> None:
        if not self.imdb_id:
            raise ValueError("IMDB ID must be provided")

    def entity_dump(self) -> Dict[str, Any]:
        """Convert entity to dictionary for persistence"""
        return {
            "title": self.title,
            "year": self.year,
            "feature_type": self.feature_type,
            "imdb_id": self.imdb_id,
            "subtitle_id": self.subtitle_id,
            "all_movie_info": self.all_movie_info,
            "upload_date": self.upload_date,
            "content": self.content,
            "language": self.language,
            "machine_translated": self.machine_translated,
            "ai_translated": self.ai_translated
        }