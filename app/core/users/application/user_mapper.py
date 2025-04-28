from typing import Dict, Any
from datetime import timezone
from app.core.users.application.dto.user_dto import UserIn, UserOut, UserProgress as UserProgressDTO, Achievement as AchievementDTO
from app.core.users.domain import UserEntity, UserProgress, Achievement

def ensure_timezone_aware(dt):
    """Ensure a datetime is timezone-aware, adding UTC if needed"""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)

class UserMapper:
    @staticmethod
    def to_entity(user_dto: UserIn) -> UserEntity:
        """Convert DTO to entity"""

        achievements = []
        for ach_dto in user_dto.achievements:
            achievements.append(Achievement.create(
                id=ach_dto.id,
                name=ach_dto.name,
                description=ach_dto.description,
                earned_at=ensure_timezone_aware(ach_dto.earned_at)
            ))
        
        progress = None
        if user_dto.progress:
            progress = UserProgress.create(
                total_practice_time_seconds=user_dto.progress.total_practice_time_seconds,
                total_dialogues=user_dto.progress.total_dialogues,
                average_pronunciation_score=user_dto.progress.average_pronunciation_score,
                average_fluency_score=user_dto.progress.average_fluency_score,
                level=user_dto.progress.level,
                xp_points=user_dto.progress.xp_points
            )
        
        return UserEntity.create(
            id=str(user_dto.id) if hasattr(user_dto, 'id') and user_dto.id else None,
            email=user_dto.email,
            name=user_dto.name,
            picture=user_dto.picture,
            google_id=user_dto.google_id,
            achievements=achievements,
            created_at=ensure_timezone_aware(user_dto.created_at),
            last_login=ensure_timezone_aware(user_dto.last_login),
            progress=progress
        )
    
    @staticmethod
    def to_dto(entity: UserEntity) -> UserOut:
        """Convert entity to DTO"""

        achievements = []
        for ach in entity.achievements:
            achievements.append(AchievementDTO(
                id=str(ach.id),
                name=ach.name,
                description=ach.description,
                earned_at=ach.earned_at
            ))
        
        progress = UserProgressDTO(
            total_practice_time_seconds=entity.progress.total_practice_time_seconds,
            total_dialogues=entity.progress.total_dialogues,
            average_pronunciation_score=entity.progress.average_pronunciation_score.value,
            average_fluency_score=entity.progress.average_fluency_score.value,
            level=entity.progress.level,
            xp_points=entity.progress.xp_points.value
        )
        
        user_dict = {
            "email": entity.email.value,
            "name": entity.name,
            "picture": entity.picture,
            "google_id": entity.google_id,
            "achievements": achievements,
            "created_at": entity.created_at,
            "last_login": entity.last_login,
            "progress": progress
        }
        
        if entity.id:
            user_dict["_id"] = entity.id.value
            
        return UserOut(**user_dict)
    
    @staticmethod
    def from_document_to_entity(doc: Dict[str, Any]) -> UserEntity:
        """Convert document directly to entity"""
        
        achievements = []
        for ach_doc in doc.get("achievements", []):
            achievements.append(Achievement.create(
                id=ach_doc["id"],
                name=ach_doc["name"],
                description=ach_doc["description"],
                earned_at=ensure_timezone_aware(ach_doc["earned_at"])
            ))

        progress_doc = doc.get("progress", {})
        progress = UserProgress.create(
            total_practice_time_seconds=progress_doc.get("total_practice_time_seconds", 0),
            total_dialogues=progress_doc.get("total_dialogues", 0),
            average_pronunciation_score=progress_doc.get("average_pronunciation_score", 0.0),
            average_fluency_score=progress_doc.get("average_fluency_score", 0.0),
            level=progress_doc.get("level", 1),
            xp_points=progress_doc.get("xp_points", 0)
        )

        return UserEntity.create(
            id=str(doc["_id"]),
            email=doc["email"],
            name=doc["name"],
            picture=doc.get("picture", ""),
            google_id=doc.get("google_id", ""),
            achievements=achievements,
            created_at=ensure_timezone_aware(doc["created_at"]),
            last_login=ensure_timezone_aware(doc["last_login"]),
            progress=progress
        )
