from typing import Any
from datetime import datetime, timezone
from app.core.common.domain.entity import Entity

class DialoguePracticeHistoryEntity(Entity):
    def __init__(
        self,
        dialogue_id: str,
        user_id: str,
        pronunciation_score: float,
        fluency_score: float,
        completed_at: datetime,
        practice_duration_seconds: float,
        character_played: str = '',
        xp_earned: int = 0,
        id: str = None
    ):
        self.id = id
        self.dialogue_id = dialogue_id
        self.user_id = user_id
        self.pronunciation_score = pronunciation_score
        self.fluency_score = fluency_score
        self.completed_at = completed_at
        self.practice_duration_seconds = practice_duration_seconds
        self.character_played = character_played
        self.xp_earned = xp_earned
        self._validate()
    
    def _validate(self) -> None:
        self._validate_scores()
        self._validate_duration()
        self._validate_completed_at()
    
    def _validate_scores(self) -> None:
        if not 0 <= self.pronunciation_score <= 1:
            raise ValueError("Pronunciation score must be between 0 and 1")
        if not 0 <= self.fluency_score <= 1:
            raise ValueError("Fluency score must be between 0 and 1")
    
    def _validate_duration(self) -> None:
        if self.practice_duration_seconds <= 0:
            raise ValueError("Practice duration must be greater than 0")
    
    def _validate_completed_at(self) -> None:
        now = datetime.now(timezone.utc)
        if self.completed_at > now:
            raise ValueError("Completed at date cannot be in the future")
    
    def entity_dump(self) -> dict[str, Any]:
        """Convert entity to dictionary for persistence"""
        return {
            "dialogue_id": self.dialogue_id,
            "user_id": self.user_id,
            "pronunciation_score": self.pronunciation_score,
            "fluency_score": self.fluency_score,
            "completed_at": self.completed_at,
            "practice_duration_seconds": self.practice_duration_seconds,
            "character_played": self.character_played,
            "xp_earned": self.xp_earned
        }