from abc import ABC, abstractmethod
from typing import TypeVar
from .domain_event import DomainEvent

# Type variable for specific event types
EventType = TypeVar('EventType', bound=DomainEvent)


class EventHandler(ABC):
    """Base class for all domain event handlers"""
    
    @abstractmethod
    async def handle(self, event: EventType) -> None:
        """Handle the specific domain event"""
        pass
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """Return the event type this handler processes"""
        pass
    
    def can_handle(self, event: DomainEvent) -> bool:
        """Check if this handler can process the given event"""
        return event.event_type == self.event_type