# Updated UserBusiness class
from fastapi import HTTPException, status
from app.core.users.application.dto.user_dto import UserOut
from app.core.dialogues.application.dto.dialogue_dto import PracticeResult
from app.core.users.infra.database.repositories import UserMongoRepository
from app.core.users.application import UserMapper

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
    ) -> None:
        """Update user's progress and check for level up"""
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