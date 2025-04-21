# app/core/dialogues/infra/database/repositories/dialogue_mongo_repo.py
from typing import List, Dict, Any, Optional
from bson import ObjectId
import logging

from app.integration.mongo import Mongo
from app.core.common.domain.repository import Repository
from app.core.dialogues.domain.dialogue_entity import DialogueEntity
from app.core.dialogues.application.dialogue_mapper import DialogueMapper

logger = logging.getLogger(__name__)

class DialogueMongoRepository(Repository[DialogueEntity]):
    """MongoDB implementation of the DialogueRepository"""
    
    async def create(self, entity: DialogueEntity) -> DialogueEntity:
        """Create a new dialogue document"""
        doc = entity.entity_dump()
        result = await Mongo.dialogues.insert_one(doc)

        entity.id = str(result.inserted_id)
        return entity
    
    async def create_many(self, entities: List[DialogueEntity]) -> List[DialogueEntity]:
        """Create multiple dialogue documents"""
        if not entities:
            return []

        docs = [entity.entity_dump() for entity in entities]
        result = await Mongo.dialogues.insert_many(docs)
 
        for i, entity in enumerate(entities):
            if i < len(result.inserted_ids):
                entity.id = str(result.inserted_ids[i])
                
        return entities
    
    async def update(self, id: str, entity: DialogueEntity) -> DialogueEntity:
        """Update an existing dialogue document"""
        doc = entity.entity_dump()

        await Mongo.dialogues.update_one(
            {"_id": ObjectId(id)},
            {"$set": doc}
        )
        
        return entity
    
    async def find_by_id(self, id: str) -> Optional[DialogueEntity]:
        """Find a dialogue by its ID"""
        if (doc := await Mongo.dialogues.find_one({"_id": ObjectId(id)})) is not None:
            return DialogueMapper.from_document_to_entity(doc)
        return None
    
    async def find_with_filters(
        self, 
        filters: Dict[str, Any], 
        skip: int = 0, 
        limit: int = 20
    ) -> List[DialogueEntity]:
        """Find dialogues matching the provided filters"""
        query = {}
        
        if "search" in filters and filters["search"]:
            search = filters["search"]
            query["$or"] = [
                {"movie.title": {"$regex": search, "$options": "i"}},
                {"lines.text": {"$regex": search, "$options": "i"}},
            ]
        
        if "imdb_id" in filters and filters["imdb_id"]:
            query["movie.imdb_id"] = filters["imdb_id"]

        cursor = Mongo.dialogues.find(query).skip(skip).limit(limit)

        return [DialogueMapper.from_document_to_entity(doc) async for doc in cursor]
    
    async def delete(self, id: str) -> bool:
        """Delete a dialogue by its ID"""
        result = await Mongo.dialogues.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
