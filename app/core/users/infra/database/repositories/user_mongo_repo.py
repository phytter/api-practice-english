from typing import List, Dict, Any, Optional
from bson import ObjectId
import logging

from app.integration.mongo import Mongo
from app.core.common.domain.repository import Repository
from app.core.users.domain import UserEntity
from app.core.users.application import UserMapper

logger = logging.getLogger(__name__)

class UserMongoRepository(Repository[UserEntity]):
    """MongoDB implementation of the UserRepository"""
    
    async def create(self, entity: UserEntity) -> UserEntity:
        """Create a new user document"""
        doc = entity.entity_dump()
        
        result = await Mongo.users.insert_one(doc)
        
        entity.id = str(result.inserted_id)
        return entity
    
    async def create_many(self, entities: List[UserEntity]) -> List[UserEntity]:
        """Create multiple user documents"""
        if not entities:
            return []
            
        docs = [entity.entity_dump() for entity in entities]
        
        result = await Mongo.users.insert_many(docs)
        
        for i, entity in enumerate(entities):
            if i < len(result.inserted_ids):
                entity.id = str(result.inserted_ids[i])
                
        return entities
    
    async def update(self, id: str, entity: UserEntity) -> UserEntity:
        """Update an existing user document"""
        doc = entity.entity_dump()
            
        await Mongo.users.update_one(
            {"_id": ObjectId(id)},
            {"$set": doc}
        )
        
        return entity
    
    async def find_by_id(self, id: str) -> Optional[UserEntity]:
        """Find a user by its ID"""
        if (doc := await Mongo.users.find_one({"_id": ObjectId(id)})) is not None:
            return UserMapper.from_document_to_entity(doc)
        return None
    
    async def find_by_google_id(self, google_id: str) -> Optional[UserEntity]:
        """Find a user by Google ID"""
        if (doc := await Mongo.users.find_one({"google_id": google_id})) is not None:
            return UserMapper.from_document_to_entity(doc)
        return None
    
    async def find_with_filters(
        self, 
        filters: Dict[str, Any], 
        skip: int = 0, 
        limit: int = 20
    ) -> List[UserEntity]:
        """Find users matching the provided filters"""
        query = {}
        
        if "email" in filters and filters["email"]:
            query["email"] = filters["email"]
        
        for key, value in filters.items():
            if key not in ["email"] and value is not None:
                query[key] = value
        
        cursor = Mongo.users.find(query).skip(skip).limit(limit)
        docs = []
        async for doc in cursor:
            docs.append(doc)
        
        return [UserMapper.from_document_to_entity(doc) for doc in docs]
    
    async def delete(self, id: str) -> bool:
        """Delete a user by its ID"""
        result = await Mongo.users.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
