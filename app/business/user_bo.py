# Updated UserBusiness class
from fastapi import HTTPException, status
import logging
from app.core.users.application.dto.user_dto import UserOut
from app.core.dialogues.application.dto.dialogue_dto import PracticeResult
from app.core.users.infra.database.repositories import UserMongoRepository
from app.core.users.application import UserMapper

logger = logging.getLogger(__name__)

class UserBusiness:
    user_repo = UserMongoRepository()

    @classmethod
    async def get_user(cls, user_id: str) -> UserOut:
        entity = await cls.user_repo.find_by_id(user_id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserMapper.to_dto(entity)

    @classmethod
    async def update_progress(
        cls,
        user_id: str,
        practice_result: PracticeResult
    ):
        """Update user's progress, publish user events, and return the user entity"""
        user_entity = await cls.user_repo.find_by_id(user_id)
        if not user_entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_entity.update_progress(
            practice_result.pronunciation_score,
            practice_result.fluency_score,
            practice_result.xp_earned
        )

        await cls.user_repo.update(user_id, user_entity)
        
        # Publish user domain events (like level up) in the appropriate business context
        await cls._publish_user_events(user_entity)
        
        return user_entity
    
    @classmethod
    async def _publish_user_events(cls, user_entity) -> None:
        """Publish user domain events"""
        from app.core.common.domain.events.event_dispatcher import event_dispatcher
        
        try:
            # Publish any user events that were raised during progress update
            user_events = user_entity.get_uncommitted_events()
            if user_events:
                await event_dispatcher.publish_all(user_events)
                user_entity.mark_events_as_committed()
        except Exception as e:
            logger.error(f"Error publishing user domain events: {str(e)}")
            # Don't re-raise - event publishing failures shouldn't break the main flow