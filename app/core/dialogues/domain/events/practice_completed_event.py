from datetime import datetime
from app.core.common.domain.events.integration_event import IntegrationEvent
from app.core.common.domain.value_objects import Uuid, Score, XpPoints


class PracticeCompletedEvent(IntegrationEvent):
    """
    Integration Event raised when a user completes a dialogue practice session.
    
    This is an Integration Event because it carries information that crosses
    bounded context boundaries and is consumed by multiple domains:
    
    - Users Domain: Updates user progress, levels, achievements
    - Dialogues Domain: Records practice history
    - Analytics Domain: Tracks user behavior and performance metrics
    - Notifications Domain: May trigger congratulatory messages
    """
    
    def __init__(
        self,
        user_id: Uuid,
        dialogue_id: Uuid,
        pronunciation_score: Score,
        fluency_score: Score,
        xp_earned: XpPoints,
        practice_duration_seconds: float,
        difficulty_level: int,
        character_played: str = "",
        occurred_at: datetime = None
    ):
        payload = {
            "user_id": str(user_id),
            "dialogue_id": str(dialogue_id),
            "pronunciation_score": pronunciation_score.value,
            "fluency_score": fluency_score.value,
            "average_score": (pronunciation_score.value + fluency_score.value) / 2,
            "xp_earned": xp_earned.value,
            "practice_duration_seconds": practice_duration_seconds,
            "difficulty_level": difficulty_level,
            "character_played": character_played
        }
        super().__init__(aggregate_id=dialogue_id, payload=payload, occurred_at=occurred_at)
    
    # Convenient properties to access payload data
    @property
    def user_id(self) -> Uuid:
        return Uuid(self.payload["user_id"])
    
    @property
    def dialogue_id(self) -> Uuid:
        return Uuid(self.payload["dialogue_id"])
    
    @property
    def pronunciation_score(self) -> float:
        return self.payload["pronunciation_score"]
    
    @property
    def fluency_score(self) -> float:
        return self.payload["fluency_score"]
    
    @property
    def average_score(self) -> float:
        return self.payload["average_score"]
    
    @property
    def xp_earned(self) -> int:
        return self.payload["xp_earned"]
    
    @property
    def practice_duration_seconds(self) -> float:
        return self.payload["practice_duration_seconds"]
    
    @property
    def difficulty_level(self) -> int:
        return self.payload["difficulty_level"]
    
    @property
    def character_played(self) -> str:
        return self.payload["character_played"]
    
    @property
    def event_type(self) -> str:
        return "dialogue.practice_completed"
    
    def __str__(self) -> str:
        return f"PracticeCompletedEvent(user_id={self.user_id}, dialogue_id={self.dialogue_id}, avg_score={self.average_score:.2f})"