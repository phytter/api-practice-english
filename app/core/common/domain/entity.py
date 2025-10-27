from abc import ABC, abstractmethod
from typing import Any, List
from app.core.common.domain.value_objects import Uuid


class Entity(ABC):
    id: Uuid
    
    def __init__(self):
        self._uncommitted_events: List['DomainEvent'] = []

    @abstractmethod
    def entity_dump(cls) -> dict[str, Any]:
        pass
    
    def raise_event(self, event: 'DomainEvent') -> None:
        """Add a domain event to the uncommitted events list"""
        self._uncommitted_events.append(event)
    
    def get_uncommitted_events(self) -> List['DomainEvent']:
        """Get all uncommitted events"""
        return self._uncommitted_events.copy()
    
    def mark_events_as_committed(self) -> None:
        """Clear the uncommitted events list"""
        self._uncommitted_events.clear()


# Import at the end to avoid circular imports
from app.core.common.domain.events.domain_event import DomainEvent
