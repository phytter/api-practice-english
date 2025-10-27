import logging
from datetime import datetime, timezone
from app.core.common.domain.events.event_handler import EventHandler
from app.core.users.domain.events.user_leveled_up_event import UserLeveledUpEvent
from app.core.users.domain.user_entity import Achievement
from app.core.users.infra.database.repositories import UserMongoRepository
from app.core.common.domain.value_objects import Uuid

logger = logging.getLogger(__name__)


class AchievementHandler(EventHandler):
    """Handles user level up events by creating achievements"""
    
    def __init__(self):
        self.user_repo = UserMongoRepository()
    
    @property
    def event_type(self) -> str:
        return "user.leveled_up"
    
    async def handle(self, event: UserLeveledUpEvent) -> None:
        """Create achievement for user level up"""
        try:
            logger.info(f"Processing UserLeveledUpEvent for user {event.user_id}: {event.old_level} -> {event.new_level}")
            
            user_entity = await self.user_repo.find_by_id(str(event.user_id))
            if not user_entity:
                logger.error(f"User {event.user_id} not found when creating level up achievement")
                return
            
            if event.new_level % 2 == 0:
                achievement = Achievement(
                    id=Uuid(),
                    name=f"Level {event.new_level} Achieved",
                    description=f"Congratulations! You've reached level {event.new_level}.",
                    earned_at=event.occurred_at
                )
                
                user_entity.achievements.append(achievement)
                
                await self.user_repo.update(str(event.user_id), user_entity)
                
                logger.info(f"Created level {event.new_level} achievement for user {event.user_id}")
            else:
                logger.debug(f"No achievement created for level {event.new_level} (not a milestone level)")
                
        except Exception as e:
            logger.error(f"Error handling UserLeveledUpEvent for user {event.user_id}: {str(e)}")
            raise