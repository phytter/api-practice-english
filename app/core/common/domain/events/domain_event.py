from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict
from app.core.common.domain.value_objects import Uuid


class DomainEvent(ABC):
    """Base class for all domain events"""
    
    def __init__(self, aggregate_id: Uuid, payload: Dict[str, Any] = None, occurred_at: datetime = None):
        self.event_id = Uuid()
        self.aggregate_id = aggregate_id
        self.occurred_at = occurred_at or datetime.now(timezone.utc)
        self.payload = payload or {}
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """Return the type identifier for this event"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary for serialization"""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "aggregate_id": str(self.aggregate_id),
            "occurred_at": self.occurred_at.isoformat(),
            "payload": self.payload
        }
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, DomainEvent):
            return False
        return self.event_id == other.event_id
    
    def __str__(self) -> str:
        return f"{self.event_type}(aggregate_id={self.aggregate_id}, occurred_at={self.occurred_at})"