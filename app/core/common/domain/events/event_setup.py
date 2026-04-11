"""Event system setup and configuration"""
import logging
from app.core.common.domain.events.event_dispatcher import event_dispatcher
from app.core.users.application.event_handlers.achievement_handler import AchievementHandler
from app.core.users.application.event_handlers.analytics_handler import AnalyticsHandler

logger = logging.getLogger(__name__)


def setup_event_handlers():
    """Register all event handlers with the global event dispatcher"""
    try:
        # Register achievement handler for user level up events
        achievement_handler = AchievementHandler()
        event_dispatcher.register_handler(achievement_handler)
        
        # Register analytics handler for practice completed events
        analytics_handler = AnalyticsHandler()
        event_dispatcher.register_handler(analytics_handler)
        
        logger.info("Domain event handlers registered successfully")
        
    except Exception as e:
        logger.error(f"Error setting up event handlers: {str(e)}")
        raise


def get_event_dispatcher():
    """Get the configured event dispatcher instance"""
    return event_dispatcher