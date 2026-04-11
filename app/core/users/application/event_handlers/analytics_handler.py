import logging
from app.core.common.domain.events.event_handler import EventHandler
from app.core.dialogues.domain.events.practice_completed_event import PracticeCompletedEvent

logger = logging.getLogger(__name__)


class AnalyticsHandler(EventHandler):
    """
    Handles PracticeCompletedEvent (Integration Event) for analytics purposes.
    
    This handler processes integration events that contain cross-domain information
    needed for analytics and insights across the entire application.
    """
    
    @property
    def event_type(self) -> str:
        return "dialogue.practice_completed"
    
    async def handle(self, event: PracticeCompletedEvent) -> None:
        """Log practice analytics data"""
        try:
            logger.info(f"Practice analytics - User: {event.user_id}, "
                       f"Dialogue: {event.dialogue_id}, "
                       f"Scores: {event.pronunciation_score:.2f}/{event.fluency_score:.2f}, "
                       f"XP: {event.xp_earned}, "
                       f"Duration: {event.practice_duration_seconds:.1f}s, "
                       f"Difficulty: {event.difficulty_level}")
            
            # In a real implementation, this could:
            # - Send data to analytics service (Google Analytics, Mixpanel, etc.)
            # - Update user statistics in a data warehouse
            # - Trigger recommendation engine updates
            # - Calculate progress streaks
            # - Update leaderboards
            
            # For now, we'll just log structured data for future processing
            analytics_data = {
                "event_type": "practice_completed",
                "user_id": str(event.user_id),
                "dialogue_id": str(event.dialogue_id),
                "pronunciation_score": event.pronunciation_score,
                "fluency_score": event.fluency_score,
                "average_score": event.average_score,
                "xp_earned": event.xp_earned,
                "practice_duration_seconds": event.practice_duration_seconds,
                "difficulty_level": event.difficulty_level,
                "character_played": event.character_played,
                "occurred_at": event.occurred_at.isoformat()
            }
            
            logger.info(f"Analytics data collected: {analytics_data}")
            
        except Exception as e:
            logger.error(f"Error handling PracticeCompletedEvent for analytics: {str(e)}")
            # Don't re-raise - analytics failures shouldn't break the main flow