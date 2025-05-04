from typing import List, Any, Optional
from datetime import datetime, timezone
from app.core.common.domain.entity import Entity
from app.core.common.domain.value_objects import Email, Score, XpPoints, Uuid

class Achievement:
    def __init__(
        self,
        id: Uuid,
        name: str,
        description: str,
        earned_at: datetime
    ):
        self.id = id
        self.name = name
        self.description = description
        self.earned_at = earned_at

    def create(
        id: str,
        name: str,
        description: str,
        earned_at: datetime
    ):
        return Achievement(Uuid(id), name, description, earned_at)

class UserProgress:
    def __init__(
        self,
        total_practice_time_seconds: int = 0,
        total_dialogues: int = 0,
        average_pronunciation_score: Score = Score(0.0),
        average_fluency_score: Score = Score(0.0),
        level: int = 1,
        xp_points: XpPoints = XpPoints(0)
    ):
        self.total_practice_time_seconds = total_practice_time_seconds
        self.total_dialogues = total_dialogues
        self.average_pronunciation_score = average_pronunciation_score
        self.average_fluency_score = average_fluency_score
        self.level = level
        self.xp_points = xp_points
        self._validate()

    def create(
        total_practice_time_seconds: int = 0,
        total_dialogues: int = 0,
        average_pronunciation_score: float = 0.0,
        average_fluency_score: float = 0.0,
        level: int = 1,
        xp_points: int = 0
    ):
        return UserProgress(
            total_practice_time_seconds=total_practice_time_seconds,
            total_dialogues=total_dialogues,
            average_pronunciation_score=Score(average_pronunciation_score),
            average_fluency_score=Score(average_fluency_score),
            level=level,
            xp_points=XpPoints(xp_points)
        )
        
    
    def _validate(self):
        if self.total_practice_time_seconds < 0:
            raise ValueError("Practice time cannot be negative")
        if self.total_dialogues < 0:
            raise ValueError("Total dialogues cannot be negative")

    def update_with_practice_result(self, pronunciation_score: float, fluency_score: float, xp_earned: int):
        """Update progress with a new practice result"""
        self.total_dialogues += 1
        self.xp_points = self.xp_points.add(xp_earned)
        
        self.average_pronunciation_score = self._calculate_average_score(
            self.average_pronunciation_score.value, pronunciation_score, self.total_dialogues
        )
        self.average_fluency_score = self._calculate_average_score(
            self.average_fluency_score.value, fluency_score, self.total_dialogues
        )
        
        self.level = self._calculate_level(self.xp_points.value)
    
    def _calculate_average_score(self, current_average: float, new_score: float, total_practices: int) -> float:
        """Calculate the new average score"""
        return Score((current_average * (total_practices - 1) + new_score) / total_practices)
    
    def _calculate_level(self, xp: int) -> int:
        """Calculate user level based on XP"""
        base_xp = 1000
        level = 1
        while xp >= base_xp:
            xp -= base_xp
            base_xp = int(base_xp * 1.2)
            level += 1
        return level

class UserEntity(Entity):
    def __init__(
        self,
        email: Email,
        name: str,
        created_at: datetime,
        last_login: datetime,
        google_id: str = '',
        picture: str = '',
        achievements: List[Achievement] = None,
        progress: UserProgress = None,
        id: Uuid = None
    ):
        self.id = id
        self.email = email
        self.name = name
        self.picture = picture
        self.google_id = google_id
        self.achievements = achievements or []
        self.created_at = created_at
        self.last_login = last_login
        self.progress = progress


    def create(
        email: str,
        name: str,
        created_at: datetime,
        last_login: datetime,
        google_id: str = '',
        picture: str = '',
        achievements: List[Achievement] = None,
        progress: UserProgress = None,
        id: str = None
    ):
        return UserEntity(
            email=Email(email),
            name=name,
            created_at=created_at,
            last_login=last_login,
            google_id=google_id,
            picture=picture,
            achievements=achievements,
            progress=progress or UserProgress(),
            id=Uuid(id)
        )

    def update_progress(self, pronunciation_score: float, fluency_score: float, xp_earned: int) -> Optional[Achievement]:
        """Update user progress and return a new achievement if earned"""
        old_level = self.progress.level
        
        self.progress.update_with_practice_result(pronunciation_score, fluency_score, xp_earned)
        
        if self.progress.level > old_level and self.progress.level % 2 == 0:
            achievement = self._create_level_up_achievement(self.progress.level)
            self.achievements.append(achievement)
            return achievement
        
        return None
    
    def _create_level_up_achievement(self, level: int) -> Achievement:
        """Create an achievement for leveling up"""
        return Achievement.create(
            name=f"Level {level} Achieved",
            description=f"Congratulations! You've reached level {level}.",
            earned_at=datetime.now(timezone.utc)
        )
    
    def entity_dump(self) -> dict[str, Any]:
        """Convert entity to dictionary for persistence"""
        return {
            "email": self.email.value,
            "name": self.name,
            "picture": self.picture,
            "google_id": self.google_id,
            "achievements": [
                {
                    "id": str(achievement.id),
                    "name": achievement.name,
                    "description": achievement.description,
                    "earned_at": achievement.earned_at
                } for achievement in self.achievements
            ],
            "created_at": self.created_at,
            "last_login": self.last_login,
            "progress": {
                "total_practice_time_seconds": self.progress.total_practice_time_seconds,
                "total_dialogues": self.progress.total_dialogues,
                "average_pronunciation_score": self.progress.average_pronunciation_score.value,
                "average_fluency_score": self.progress.average_fluency_score.value,
                "level": self.progress.level,
                "xp_points": self.progress.xp_points.value
            }
        }