from typing import List, Any, Optional
from app.core.common.domain.entity import Entity

class DialogueLine:
    def __init__(self, character: str, text: str, start_time: float, end_time: float):
        self.character = character
        self.text = text
        self.start_time = start_time
        self.end_time = end_time
        self._validate_timestamp()
    
    def _validate_timestamp(self) -> None:
        if self.start_time < 0:
            raise ValueError("Start time cannot be negative")
        if self.end_time < self.start_time:
            raise ValueError("End time must be greater than start time")

class DialogueMovie:
    def __init__(self, imdb_id: str, title: str, language: str = "en"):
        self.imdb_id = imdb_id
        self.title = title
        self.language = language

class DialogueEntity(Entity):
    def __init__(
        self, 
        difficulty_level: int,
        duration_seconds: float,
        lines: List[DialogueLine],
        movie: Optional[DialogueMovie] = None,
        id: str = None
    ):
        self.id = id
        self.movie = movie
        self.difficulty_level = difficulty_level
        self.duration_seconds = duration_seconds
        self.lines = lines
        self._validate()

    def create(
        difficulty_level: int,
        duration_seconds: float,
        lines: List[DialogueLine],
        movie: Optional[DialogueMovie] = None,
        id: str = None
    ):
        return DialogueEntity(difficulty_level, duration_seconds, lines, movie, id)
    
    def _validate(self) -> None:
        self._validate_difficulty_level()
        self._validate_lines()
    
    def _validate_difficulty_level(self) -> None:
        if not 1 <= self.difficulty_level <= 5:
            raise ValueError("Difficulty level must be between 1 and 5")
    
    def _validate_lines(self) -> None:
        if not self.lines:
            raise ValueError("Dialogue must have at least one line")
        
        # Check if duration makes sense with the lines
        if self.lines:
            calculated_duration = self.lines[-1].end_time - self.lines[0].start_time
            if abs(calculated_duration - self.duration_seconds) > 1.0:  # 1 second tolerance
                raise ValueError("Duration doesn't match the dialogue lines timing")
    
    def entity_dump(self) -> dict[str, Any]:
        """Convert entity to dictionary for persistence"""
        return {
            "movie": {
                "imdb_id": self.movie.imdb_id,
                "title": self.movie.title,
                "language": self.movie.language
            } if self.movie else None,
            "difficulty_level": self.difficulty_level,
            "duration_seconds": self.duration_seconds,
            "lines": [
                {
                    "character": line.character,
                    "text": line.text,
                    "start_time": line.start_time,
                    "end_time": line.end_time
                } for line in self.lines
            ]
        }