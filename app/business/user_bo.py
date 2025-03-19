from fastapi import HTTPException, status
from app.model import ObjectId, UserOut, PracticeResult, Achievement
from app.integration.mongo import Mongo
from datetime import datetime, timezone

class UserBusiness:

    @classmethod
    async def get_user(cls, user_id: str) -> UserOut:
        if (user := await Mongo.users.find_one({"_id": ObjectId(user_id)})) is not None:
            return UserOut(**user)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    @classmethod
    async def update_progress(
        cls,
        user_id: str,
        practice_result: PracticeResult
    ) -> None:
        """Update user's progress and check for level up"""
        user = await cls.get_user(user_id)
        progress = user.progress

        progress.total_dialogues += 1
        progress.xp_points += practice_result.xp_earned

        total_practices = progress.total_dialogues
        progress.average_pronunciation_score = cls._calculate_average_score(
            progress.average_pronunciation_score, practice_result.pronunciation_score, total_practices
        )
        progress.average_fluency_score = cls._calculate_average_score(
            progress.average_fluency_score, practice_result.fluency_score, total_practices
        )

        new_level = cls._calculate_level(progress.xp_points)
        if new_level > progress.level:
            progress.level = new_level
            achievement = cls._create_level_up_achievement(new_level)
            if achievement:
                user.achievements.append(achievement)

        await Mongo.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
				"progress": progress.model_dump(),
				"achievements": [ach.model_dump() for ach in user.achievements]
			}}
        )

    @staticmethod
    def _calculate_average_score(current_average: float, new_score: float, total_practices: int) -> float:
        """Calculate the new average score"""
        return (current_average * (total_practices - 1) + new_score) / total_practices

    @staticmethod
    def _calculate_level(xp: int) -> int:
        """Calculate user level based on XP"""
        base_xp = 1000
        level = 1
        while xp >= base_xp:
            xp -= base_xp
            base_xp = int(base_xp * 1.2)
            level += 1
        return level

    @staticmethod
    def _create_level_up_achievement(level: int) -> Achievement:
        """Create an achievement for leveling up"""
        if level % 2 != 0:
            return None
        return Achievement(
            id=f"level_{level}",
            name=f"Level {level} Achieved",
            description=f"Congratulations! You've reached level {level}.",
            earned_at=datetime.now(timezone.utc)
        )
