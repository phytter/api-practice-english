import logging
from typing import List, Dict, Type
from .domain_event import DomainEvent
from .event_handler import EventHandler

logger = logging.getLogger(__name__)


class EventDispatcher:
    """Simple in-memory event dispatcher for domain events"""
    
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
    
    def register_handler(self, handler: EventHandler) -> None:
        """Register an event handler for a specific event type"""
        event_type = handler.event_type
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Registered handler {handler.__class__.__name__} for event type {event_type}")
    
    def unregister_handler(self, handler: EventHandler) -> None:
        """Unregister an event handler"""
        event_type = handler.event_type
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                if not self._handlers[event_type]:
                    del self._handlers[event_type]
                logger.info(f"Unregistered handler {handler.__class__.__name__} for event type {event_type}")
            except ValueError:
                logger.warning(f"Handler {handler.__class__.__name__} was not registered for event type {event_type}")
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish a single domain event to all registered handlers"""
        event_type = event.event_type
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers registered for event type {event_type}")
            return
        
        # Log differently for integration events vs domain events
        event_category = "INTEGRATION" if getattr(event, 'is_integration_event', False) else "DOMAIN"
        logger.info(f"Publishing {event_category} event {event_type} to {len(handlers)} handler(s)")
        
        for handler in handlers:
            try:
                await handler.handle(event)
                logger.debug(f"Handler {handler.__class__.__name__} processed {event_category} event {event_type}")
            except Exception as e:
                logger.error(f"Error in handler {handler.__class__.__name__} for {event_category} event {event_type}: {str(e)}")
                # Integration events may need more sophisticated error handling (retry, DLQ)
                # Domain events typically fail fast within the same bounded context
    
    async def publish_all(self, events: List[DomainEvent]) -> None:
        """Publish multiple domain events"""
        for event in events:
            await self.publish(event)
    
    def get_registered_handlers(self, event_type: str = None) -> Dict[str, List[EventHandler]]:
        """Get all registered handlers, optionally filtered by event type"""
        if event_type:
            return {event_type: self._handlers.get(event_type, [])}
        return self._handlers.copy()


# Global instance for the application
event_dispatcher = EventDispatcher()