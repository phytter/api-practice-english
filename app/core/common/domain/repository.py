from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Dict, Any, Optional

T = TypeVar('T')

class Repository(Generic[T], ABC):
    """Base repository interface that defines common CRUD operations"""
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity"""
        pass
    
    @abstractmethod
    async def create_many(self, entities: List[T]) -> List[T]:
        """Create multiple entities"""
        pass
    
    @abstractmethod
    async def update(self, id: str, entity: T) -> T:
        """Update an existing entity"""
        pass
    
    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[T]:
        """Find an entity by its ID"""
        pass
    
    @abstractmethod
    async def find_with_filters(self, filters: Dict[str, Any], skip: int = 0, limit: int = 20) -> List[T]:
        """Find entities matching the provided filters"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete an entity by its ID"""
        pass