from datetime import datetime
from app.core.common.domain.events.domain_event import DomainEvent
from app.core.common.domain.value_objects import Uuid, XpPoints


class UserLeveledUpEvent(DomainEvent):
    """Event raised when a user levels up"""
    
    def __init__(
        self,
        user_id: Uuid,
        old_level: int,
        new_level: int,
        total_xp: XpPoints,
        occurred_at: datetime = None
    ):
        payload = {
            "user_id": str(user_id),
            "old_level": old_level,
            "new_level": new_level,
            "levels_gained": new_level - old_level,
            "total_xp": total_xp.value
        }
        super().__init__(aggregate_id=user_id, payload=payload, occurred_at=occurred_at)
    
    # Convenient properties to access payload data
    @property
    def user_id(self) -> Uuid:
        return Uuid(self.payload["user_id"])
    
    @property
    def old_level(self) -> int:
        return self.payload["old_level"]
    
    @property
    def new_level(self) -> int:
        return self.payload["new_level"]
    
    @property
    def levels_gained(self) -> int:
        return self.payload["levels_gained"]
    
    @property
    def total_xp(self) -> int:
        return self.payload["total_xp"]
    
    @property
    def event_type(self) -> str:
        return "user.leveled_up"
    
    def __str__(self) -> str:
        return f"UserLeveledUpEvent(user_id={self.user_id}, {self.old_level} -> {self.new_level})"