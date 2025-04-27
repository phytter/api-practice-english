from typing import Dict, Any
from dateutil import parser
from app.core.movies.application.dto.movie_dto import MovieIn, MovieOut
from app.core.movies.domain import MovieEntity
from app.core.common.application.dto import MongoObjectId

class MovieMapper:
    @staticmethod
    def to_entity(movie_dto: MovieIn) -> MovieEntity:
        """Convert DTO to entity"""

        return MovieEntity(
            id=str(movie_dto.id) if movie_dto.id else None,
            title=movie_dto.title,
            year=movie_dto.year,
            feature_type=movie_dto.feature_type,
            imdb_id=movie_dto.imdb_id,
            subtitle_id=movie_dto.subtitle_id,
            all_movie_info=movie_dto.all_movie_info,
            upload_date=movie_dto.upload_date,
            content=movie_dto.content,
            language=movie_dto.language,
            machine_translated=movie_dto.machine_translated,
            ai_translated=movie_dto.ai_translated
        )
    
    @staticmethod
    def to_dto(entity: MovieEntity) -> MovieOut:
        """Convert entity to DTO"""
        movie_dict = {
            "title": entity.title,
            "year": entity.year,
            "feature_type": entity.feature_type,
            "imdb_id": entity.imdb_id,
            "subtitle_id": entity.subtitle_id,
            "all_movie_info": entity.all_movie_info,
            "upload_date": entity.upload_date,
            "content": entity.content,
            "language": entity.language,
            "machine_translated": entity.machine_translated,
            "ai_translated": entity.ai_translated
        }
        
        if entity.id:
            movie_dict["_id"] = MongoObjectId(entity.id)
            
        return MovieOut(**movie_dict)
    
    @staticmethod
    def from_document_to_entity(doc: Dict[str, Any]) -> MovieEntity:
        """Convert MongoDB document directly to entity"""
        
        return MovieEntity(
            id=str(doc["_id"]),
            title=doc["title"],
            year=doc["year"],
            feature_type=doc["feature_type"],
            imdb_id=doc["imdb_id"],
            subtitle_id=doc["subtitle_id"],
            all_movie_info=doc["all_movie_info"],
            upload_date=parser.parse(doc["upload_date"]),
            content=doc["content"],
            language=doc.get("language", "en"),
            machine_translated=doc.get("machine_translated", False),
            ai_translated=doc.get("ai_translated", False)
        )
