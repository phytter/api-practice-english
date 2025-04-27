from typing import Dict, Any
from dateutil import parser
from datetime import datetime, timezone
from app.core.dialogues.application.dto.dialogue_dto import DialoguePracticeHistoryIn, DialoguePracticeHistoryOut
from app.core.dialogues.domain.dialogue_practice_history_entity import DialoguePracticeHistoryEntity
from app.core.dialogues.application.dialogue_mapper import DialogueMapper
from app.core.common.application.dto import MongoObjectId

class DialoguePracticeHistoryMapper:
    @staticmethod
    def to_entity(practice_dto: DialoguePracticeHistoryIn) -> DialoguePracticeHistoryEntity:
        """Convert DTO to entity"""
        return DialoguePracticeHistoryEntity.create(
            id=str(practice_dto.id) if hasattr(practice_dto, 'id') and practice_dto.id else None,
            dialogue_id=practice_dto.dialogue_id,
            user_id=practice_dto.user_id,
            pronunciation_score=practice_dto.pronunciation_score,
            fluency_score=practice_dto.fluency_score,
            completed_at=practice_dto.completed_at,
            practice_duration_seconds=practice_dto.practice_duration_seconds,
            character_played=practice_dto.character_played,
            xp_earned=practice_dto.xp_earned
        )
    
    @staticmethod
    def to_dto(entity: DialoguePracticeHistoryEntity, include_dialogue: bool = False) -> DialoguePracticeHistoryOut:
        """Convert entity to DTO"""
        
        dto_dict = {
            "dialogue_id": entity.dialogue_id,
            "user_id": entity.user_id,
            "pronunciation_score": entity.pronunciation_score.value,
            "fluency_score": entity.fluency_score.value,
            "completed_at": entity.completed_at,
            "practice_duration_seconds": entity.practice_duration_seconds,
            "character_played": entity.character_played,
            "xp_earned": entity.xp_earned.value
        }
        
        if entity.id:
            dto_dict["_id"] = MongoObjectId(entity.id)
        
        if include_dialogue and hasattr(entity, 'dialogue') and entity.dialogue:
            dto_dict["dialogue"] = DialogueMapper.to_dto(entity.dialogue)

        return DialoguePracticeHistoryOut(**dto_dict)
    
    @staticmethod
    def from_document_to_entity(doc: Dict[str, Any]) -> DialoguePracticeHistoryEntity:
        """Convert MongoDB document directly to entity"""
        completed_at = doc["completed_at"]
        if isinstance(completed_at, str):
            try:
                completed_at = parser.parse(completed_at)
                completed_at = completed_at.replace(tzinfo=timezone.utc)
            except Exception as e:
                completed_at = datetime.now(timezone.utc)

        return DialoguePracticeHistoryEntity.create(
            id=str(doc["_id"]),
            dialogue_id=doc["dialogue_id"],
            user_id=doc["user_id"],
            pronunciation_score=doc["pronunciation_score"],
            fluency_score=doc["fluency_score"],
            completed_at=completed_at,
            practice_duration_seconds=doc["practice_duration_seconds"],
            character_played=doc.get("character_played", ""),
            xp_earned=doc.get("xp_earned", 0)
        )
