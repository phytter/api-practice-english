from typing import Dict, Any
from app.core.dialogues.application.dto.dialogue_dto import DialogueIn, DialogueOut
from app.core.dialogues.domain.dialogue_entity import DialogueEntity, DialogueLine, DialogueMovie

class DialogueMapper:
    @staticmethod
    def to_entity(dialogue_dto: DialogueIn) -> DialogueEntity:
        """Convert DTO to entity"""
        movie = None
        if dialogue_dto.movie:
            movie = DialogueMovie(
                imdb_id=dialogue_dto.movie.imdb_id,
                title=dialogue_dto.movie.title,
                language=dialogue_dto.movie.language
            )
        
        lines = [
            DialogueLine(
                character=line.character,
                text=line.text,
                start_time=line.start_time,
                end_time=line.end_time
            ) for line in dialogue_dto.lines
        ]
        
        return DialogueEntity.create(
            difficulty_level=dialogue_dto.difficulty_level,
            duration_seconds=dialogue_dto.duration_seconds,
            lines=lines,
            movie=movie,
            id=str(dialogue_dto.id) if hasattr(dialogue_dto, 'id') and dialogue_dto.id else None
        )
    
    @staticmethod
    def to_dto(entity: DialogueEntity) -> DialogueOut:
        """Convert entity to DTO"""
        dto_dict = {
            "difficulty_level": entity.difficulty_level,
            "duration_seconds": entity.duration_seconds,
            "lines": [
                {
                    "character": line.character,
                    "text": line.text,
                    "start_time": line.start_time,
                    "end_time": line.end_time
                } for line in entity.lines
            ]
        }
        
        if entity.movie:
            dto_dict["movie"] = {
                "imdb_id": entity.movie.imdb_id,
                "title": entity.movie.title,
                "language": entity.movie.language
            }
        
        if entity.id:
            dto_dict["_id"] = entity.id.value
            
        return DialogueOut(**dto_dict)
    
    @staticmethod
    def from_document_to_entity(doc: Dict[str, Any]) -> DialogueEntity:
        """Convert MongoDB document directly to entity"""
 
        movie = None
        if doc.get("movie"):
            movie_data = doc["movie"]
            movie = DialogueMovie(
                imdb_id=movie_data["imdb_id"],
                title=movie_data["title"],
                language=movie_data.get("language", "en")
            )
        
        lines = []
        for line_data in doc.get("lines", []):
            lines.append(DialogueLine(
                character=line_data.get("character", ""),
                text=line_data["text"],
                start_time=line_data["start_time"],
                end_time=line_data["end_time"]
            ))
        
        return DialogueEntity.create(
            id=str(doc["_id"]),
            movie=movie,
            difficulty_level=doc["difficulty_level"],
            duration_seconds=doc["duration_seconds"],
            lines=lines
        )
