from abc import ABC
from datetime import datetime
from typing import Dict, Any
from .domain_event import DomainEvent


class IntegrationEvent(DomainEvent, ABC):
    """
    Base class for Integration Events.
    
    Integration Events are events that cross bounded context boundaries
    and are used to communicate between different domains/bounded contexts.
    They typically contain information that multiple domains need to react to.
    
    Examples:
    - PracticeCompletedEvent: Contains practice data needed by users (for progress),
      dialogues (for history), and analytics (for insights)
    """
    
    def __init__(self, aggregate_id, payload: Dict[str, Any] = None, occurred_at: datetime = None):
        super().__init__(aggregate_id, payload, occurred_at)
        
    @property
    def is_integration_event(self) -> bool:
        """Mark this as an integration event"""
        return True
        
    def __str__(self) -> str:
        return f"[INTEGRATION] {super().__str__()}"