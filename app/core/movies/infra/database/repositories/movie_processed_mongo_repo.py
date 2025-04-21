from typing import List, Dict, Any, Optional
from bson import ObjectId
import logging

from app.integration.mongo import Mongo
from app.core.common.domain.repository import Repository
from app.core.movies.domain import MovieEntity
from app.core.movies.application import MovieMapper

logger = logging.getLogger(__name__)

class MovieProcessedMongoRepository(Repository[MovieEntity]):
    """MongoDB implementation of the MovieProcessedMongoRepository"""
    
    async def create(self, entity: MovieEntity) -> MovieEntity:
        """Create a new movie document"""
        doc = entity.entity_dump()
        result = await Mongo.movies_processed.insert_one(doc)
        
        entity.id = str(result.inserted_id)
        return entity
    
    async def create_many(self, entities: List[MovieEntity]) -> List[MovieEntity]:
        """Create multiple movie documents"""
        if not entities:
            return []
            
        docs = [entity.entity_dump() for entity in entities]
        
        result = await Mongo.movies_processed.insert_many(docs)
        
        for i, entity in enumerate(entities):
            if i < len(result.inserted_ids):
                entity.id = str(result.inserted_ids[i])
                
        return entities
    
    async def update(self, id: str, entity: MovieEntity) -> MovieEntity:
        """Update an existing movie document"""
        doc = entity.entity_dump()
            
        await Mongo.movies_processed.update_one(
            {"_id": ObjectId(id)},
            {"$set": doc}
        )
        
        return entity
    
    async def find_by_id(self, id: str) -> Optional[MovieEntity]:
        """Find a movie by its ID"""
        doc = await Mongo.movies_processed.find_one({"_id": ObjectId(id)})
        return MovieMapper.from_document_to_entity(doc) if doc else None
    
    async def find_by_imdb_id(self, imdb_id: str) -> Optional[MovieEntity]:
        """Find a movie by IMDB ID"""
        doc = await Mongo.movies_processed.find_one({"imdb_id": imdb_id})
        return MovieMapper.from_document_to_entity(doc) if doc else None
    
    async def find_with_filters(
        self, 
        filters: Dict[str, Any], 
        skip: int = 0, 
        limit: int = 20
    ) -> List[MovieEntity]:
        """Find movies matching the provided filters"""
        query = {}
        
        if "title" in filters and filters["title"]:
            query["title"] = {"$regex": filters["title"], "$options": "i"}
        
        if "imdb_id" in filters and filters["imdb_id"]:
            query["imdb_id"] = filters["imdb_id"]
            
        for key, value in filters.items():
            if key not in ["title", "imdb_id"] and value is not None:
                query[key] = value
        
        cursor = Mongo.movies_processed.find(query).skip(skip).limit(limit)
        
        return [MovieMapper.from_document_to_entity(doc) async for doc in cursor]
    
    async def delete(self, id: str) -> bool:
        """Delete a movie by its ID"""
        result = await Mongo.movies_processed.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0