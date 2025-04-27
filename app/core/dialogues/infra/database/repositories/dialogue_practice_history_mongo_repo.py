from typing import List, Dict, Any, Optional
from bson import ObjectId
import logging

from app.integration.mongo import Mongo
from app.core.dialogues.domain import DialoguePracticeHistoryEntity, DialoguePracticeHistoryRepository
from app.core.dialogues.application import DialogueMapper, DialoguePracticeHistoryMapper

logger = logging.getLogger(__name__)

class DialoguePracticeHistoryMongoRepository(DialoguePracticeHistoryRepository):
    """MongoDB implementation of the DialoguePracticeHistoryRepository"""
    
    async def create(self, entity: DialoguePracticeHistoryEntity) -> DialoguePracticeHistoryEntity:
        """Create a new practice history document"""
        doc = entity.entity_dump()
        
        result = await Mongo.dialogue_practice_history.insert_one(doc)
        
        entity.id = str(result.inserted_id)
        return entity
    
    async def create_many(self, entities: List[DialoguePracticeHistoryEntity]) -> List[DialoguePracticeHistoryEntity]:
        """Create multiple practice history documents"""
        if not entities:
            return []
            
        docs = [entity.entity_dump() for entity in entities]
        
        result = await Mongo.dialogue_practice_history.insert_many(docs)
        
        for i, entity in enumerate(entities):
            if i < len(result.inserted_ids):
                entity.id = str(result.inserted_ids[i])
                
        return entities
    
    async def update(self, id: str, entity: DialoguePracticeHistoryEntity) -> DialoguePracticeHistoryEntity:
        """Update an existing practice history document"""
        doc = entity.entity_dump()
            
        await Mongo.dialogue_practice_history.update_one(
            {"_id": ObjectId(id)},
            {"$set": doc}
        )
        
        return entity
    
    async def find_by_id(self, id: str) -> Optional[DialoguePracticeHistoryEntity]:
        """Find a practice history by its ID"""
        try:
            if (doc := await Mongo.dialogue_practice_history.find_one({"_id": ObjectId(id)})) is not None:
                return DialoguePracticeHistoryMapper.from_document_to_entity(doc)
            return None
        except Exception as e:
            logger.error(f"Error finding practice history by ID: {str(e)}")
            return None
    
    async def find_with_filters(
        self, 
        filters: Dict[str, Any], 
        skip: int = 0, 
        limit: int = 20,
        include_dialogue: bool = False
    ) -> List[DialoguePracticeHistoryEntity]:
        """Find practice histories matching the provided filters"""
        query = {}
        
        if "user_id" in filters and filters["user_id"]:
            query["user_id"] = filters["user_id"]
            
        if "dialogue_id" in filters and filters["dialogue_id"]:
            query["dialogue_id"] = filters["dialogue_id"]
            
        sort_field = filters.get("sort_field", "completed_at")
        sort_direction = -1 if filters.get("sort_desc", True) else 1

        if include_dialogue:
            return await self._find_with_dialogues(query, sort_field, sort_direction, skip, limit)
        else:
            cursor = Mongo.dialogue_practice_history.find(query).sort(sort_field, sort_direction).skip(skip).limit(limit)
            docs = []
            async for doc in cursor:
                docs.append(doc)
            
            return [DialoguePracticeHistoryMapper.from_document_to_entity(doc) for doc in docs]
                
    
    async def delete(self, id: str) -> bool:
        """Delete a practice history by its ID"""
        result = await Mongo.dialogue_practice_history.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
    
    async def _find_with_dialogues(self, query: Dict, sort_field: str, sort_direction: int, skip: int, limit: int) -> List[DialoguePracticeHistoryEntity]:
        """Find practice histories with their associated dialogues"""
        
        pipeline = [
            {"$match": query},
            {"$sort": {sort_field: sort_direction}},
            {"$skip": skip},
            {"$limit": limit},
            {
                "$addFields": {
                    "dialogue_object_id": {"$toObjectId": "$dialogue_id"}
                }
            },
            {
                "$lookup": {
                    "from": "dialogues",
                    "localField": "dialogue_object_id",
                    "foreignField": "_id",
                    "as": "dialogue"
                }
            },
            {
                "$addFields": {
                    "dialogue": {"$arrayElemAt": ["$dialogue", 0]}
                }
            }
        ]

        practice_histories = []
        
        cursor = Mongo.dialogue_practice_history.aggregate(pipeline)
        async for doc in cursor:
            practice_entity = DialoguePracticeHistoryMapper.from_document_to_entity(doc)
            if "dialogue" in doc and doc["dialogue"]:
                dialogue_entity = DialogueMapper.from_document_to_entity(doc["dialogue"])
                practice_entity.dialogue = dialogue_entity
            
            practice_histories.append(practice_entity)

        return practice_histories