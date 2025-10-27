import pytest
from datetime import datetime, timezone
from app.core.common.domain.events.event_dispatcher import EventDispatcher
from app.core.users.domain.events.user_leveled_up_event import UserLeveledUpEvent
from app.core.dialogues.domain.events.practice_completed_event import PracticeCompletedEvent
from app.core.users.application.event_handlers.achievement_handler import AchievementHandler
from app.core.users.application.event_handlers.analytics_handler import AnalyticsHandler
from app.core.common.domain.value_objects import Uuid, Score, XpPoints
from app.core.users.domain.user_entity import UserEntity, UserProgress
from app.core.common.domain.value_objects import Email


class TestDomainEvents:
    """Test domain events functionality"""
    
    def test_user_leveled_up_event_creation(self):
        """Test UserLeveledUpEvent creation and properties"""
        user_id = Uuid()
        event = UserLeveledUpEvent(
            user_id=user_id,
            old_level=1,
            new_level=3,
            total_xp=XpPoints(2500)
        )
        
        assert event.user_id == user_id
        assert event.old_level == 1
        assert event.new_level == 3
        assert event.levels_gained == 2
        assert event.total_xp == 2500
        assert event.event_type == "user.leveled_up"
        assert event.aggregate_id == user_id
    
    def test_practice_completed_event_creation(self):
        """Test PracticeCompletedEvent creation and properties"""
        user_id = Uuid()
        dialogue_id = Uuid()
        event = PracticeCompletedEvent(
            user_id=user_id,
            dialogue_id=dialogue_id,
            pronunciation_score=Score(0.85),
            fluency_score=Score(0.78),
            xp_earned=XpPoints(150),
            practice_duration_seconds=45.5,
            difficulty_level=3,
            character_played="Alice"
        )
        
        assert event.user_id == user_id
        assert event.dialogue_id == dialogue_id
        assert event.pronunciation_score == 0.85
        assert event.fluency_score == 0.78
        assert event.xp_earned == 150
        assert event.practice_duration_seconds == 45.5
        assert event.difficulty_level == 3
        assert event.character_played == "Alice"
        assert event.average_score == 0.815  # (0.85 + 0.78) / 2
        assert event.event_type == "dialogue.practice_completed"
    
    def test_event_dispatcher_registration(self):
        """Test event handler registration with dispatcher"""
        dispatcher = EventDispatcher()
        handler = AchievementHandler()
        
        dispatcher.register_handler(handler)
        handlers = dispatcher.get_registered_handlers("user.leveled_up")
        
        assert "user.leveled_up" in handlers
        assert len(handlers["user.leveled_up"]) == 1
        assert handlers["user.leveled_up"][0] == handler
    
    @pytest.mark.asyncio
    async def test_event_dispatcher_publish(self):
        """Test event publishing through dispatcher"""
        dispatcher = EventDispatcher()
        
        # Create a mock handler to track calls
        class MockHandler:
            def __init__(self):
                self.handled_events = []
                
            @property
            def event_type(self):
                return "user.leveled_up"
                
            def can_handle(self, event):
                return event.event_type == self.event_type
                
            async def handle(self, event):
                self.handled_events.append(event)
        
        mock_handler = MockHandler()
        dispatcher.register_handler(mock_handler)
        
        # Create and publish event
        event = UserLeveledUpEvent(
            user_id=Uuid(),
            old_level=1,
            new_level=2,
            total_xp=XpPoints(1500)
        )
        
        await dispatcher.publish(event)
        
        assert len(mock_handler.handled_events) == 1
        assert mock_handler.handled_events[0] == event
    
    def test_user_entity_raises_level_up_event(self):
        """Test that UserEntity raises UserLeveledUpEvent when leveling up"""
        user = UserEntity(
            email=Email("test@example.com"),
            name="Test User",
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
            progress=UserProgress(level=1, xp_points=XpPoints(900))
        )
        
        # Trigger level up by updating progress with enough XP
        user.update_progress(pronunciation_score=0.9, fluency_score=0.8, xp_earned=200)
        
        # Check that event was raised
        events = user.get_uncommitted_events()
        assert len(events) == 1
        assert isinstance(events[0], UserLeveledUpEvent)
        assert events[0].old_level == 1
        assert events[0].new_level == 2
    
    def test_user_entity_no_event_when_no_level_change(self):
        """Test that UserEntity doesn't raise events when not leveling up"""
        user = UserEntity(
            email=Email("test@example.com"),
            name="Test User",
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
            progress=UserProgress(level=1, xp_points=XpPoints(500))
        )
        
        # Update progress but not enough to level up
        user.update_progress(pronunciation_score=0.7, fluency_score=0.6, xp_earned=100)
        
        # Check that no events were raised
        events = user.get_uncommitted_events()
        assert len(events) == 0
    
    def test_event_serialization(self):
        """Test event serialization to dictionary"""
        event = UserLeveledUpEvent(
            user_id=Uuid(),
            old_level=2,
            new_level=4,
            total_xp=XpPoints(3000),
            occurred_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["event_type"] == "user.leveled_up"
        assert event_dict["payload"]["old_level"] == 2
        assert event_dict["payload"]["new_level"] == 4
        assert event_dict["payload"]["levels_gained"] == 2
        assert event_dict["payload"]["total_xp"] == 3000
        assert "event_id" in event_dict
        assert "aggregate_id" in event_dict
        assert "occurred_at" in event_dict
    
    def test_event_equality(self):
        """Test event equality based on event_id"""
        user_id = Uuid()
        event1 = UserLeveledUpEvent(user_id=user_id, old_level=1, new_level=2, total_xp=XpPoints(1500))
        event2 = UserLeveledUpEvent(user_id=user_id, old_level=1, new_level=2, total_xp=XpPoints(1500))
        
        # Events with different IDs should not be equal
        assert event1 != event2
        
        # Event should be equal to itself
        assert event1 == event1