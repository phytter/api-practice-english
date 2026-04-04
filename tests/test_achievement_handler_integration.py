import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from app.business.dialogue_bo import DialogueBusiness
from app.business.user_bo import UserBusiness
from app.core.users.domain.user_entity import UserEntity, UserProgress, Achievement
from app.core.users.application.event_handlers.achievement_handler import AchievementHandler
from app.core.users.domain.events.user_leveled_up_event import UserLeveledUpEvent
from app.core.dialogues.application.dto.dialogue_dto import PracticeResult, DialogueOut, DialogueLine, DialogueMovie
from app.core.users.application.dto.user_dto import UserOut
from app.core.common.domain.events.event_dispatcher import EventDispatcher
from app.core.common.domain.value_objects import Email, Uuid, XpPoints, Score


class TestAchievementHandlerIntegration:
    """Comprehensive integration tests for the achievement handler flow"""
    
    @pytest.fixture
    def sample_user_entity(self):
        """Create a sample user entity for testing"""
        return UserEntity(
            id=Uuid(),
            email=Email("test@example.com"),
            name="Test User",
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
            progress=UserProgress(level=1, xp_points=XpPoints(800))  # Close to level 2
        )
    
    @pytest.fixture
    def sample_user_dto(self, sample_user_entity):
        """Create a sample user DTO for testing"""
        return UserOut(
            _id=str(sample_user_entity.id),
            email=sample_user_entity.email.value,
            name=sample_user_entity.name,
            picture=sample_user_entity.picture,
            google_id=sample_user_entity.google_id,
            achievements=[],
            created_at=sample_user_entity.created_at,
            last_login=sample_user_entity.last_login,
            progress={
                "level": sample_user_entity.progress.level,
                "xp_points": sample_user_entity.progress.xp_points.value,
                "total_dialogues": sample_user_entity.progress.total_dialogues,
                "average_pronunciation_score": sample_user_entity.progress.average_pronunciation_score.value,
                "average_fluency_score": sample_user_entity.progress.average_fluency_score.value,
                "total_practice_time_seconds": sample_user_entity.progress.total_practice_time_seconds
            }
        )
    
    @pytest.fixture
    def sample_practice_result(self):
        """Create a sample practice result that will cause level up"""
        return PracticeResult(
            pronunciation_score=0.85,
            fluency_score=0.80,
            transcribed_text="Hello world",
            word_timings=[],
            suggestions=[],
            xp_earned=5000  # Definitely enough to level up many times
        )
    
    @pytest.fixture
    def sample_dialogue(self):
        """Create a sample dialogue for testing"""
        return DialogueOut(
            _id=str(Uuid()),
            movie=DialogueMovie(
                title="Test Movie",
                imdb_id="tt1234567"
            ),
            difficulty_level=10,
            duration_seconds=120.0,
            lines=[
                DialogueLine(
                    character="Alice",
                    text="Hello world",
                    start_time=0.0,
                    end_time=2.0
                )
            ]
        )
    
    @pytest.fixture
    def event_dispatcher(self):
        """Create a fresh event dispatcher for each test"""
        return EventDispatcher()
    
    @pytest.fixture
    def achievement_handler(self):
        """Create an achievement handler instance"""
        return AchievementHandler()

    # HIGH PRIORITY TESTS
    
    @pytest.mark.asyncio
    async def test_achievement_handler_triggered_on_level_up(
        self, 
        sample_user_entity, 
        event_dispatcher, 
        achievement_handler
    ):
        """Test that AchievementHandler is properly triggered when a user levels up"""
        # Setup
        event_dispatcher.register_handler(achievement_handler)
        
        # Mock the user repository
        with patch.object(achievement_handler, 'user_repo') as mock_repo:
            mock_repo.find_by_id = AsyncMock(return_value=sample_user_entity)
            mock_repo.update = AsyncMock(return_value=None)
            
            # Create level up event (level 2 = milestone)
            event = UserLeveledUpEvent(
                user_id=sample_user_entity.id,
                old_level=1,
                new_level=2,
                total_xp=XpPoints(1200)
            )
            
            # Act
            await event_dispatcher.publish(event)
            
            # Assert
            mock_repo.find_by_id.assert_called_once_with(str(sample_user_entity.id))
            mock_repo.update.assert_called_once()
            
            # Verify achievement was added
            updated_user = mock_repo.update.call_args[0][1]
            assert len(updated_user.achievements) == 1
            assert updated_user.achievements[0].name == "Level 2 Achieved"
    
    @pytest.mark.asyncio
    async def test_achievement_creation_for_milestone_levels(
        self, 
        sample_user_entity, 
        achievement_handler
    ):
        """Test achievement creation for milestone levels (even levels only)"""
        even_levels = [2, 4, 6, 8, 10]
        
        for level in even_levels:
            # Reset achievements
            sample_user_entity.achievements = []
            
            with patch.object(achievement_handler, 'user_repo') as mock_repo:
                mock_repo.find_by_id = AsyncMock(return_value=sample_user_entity)
                mock_repo.update = AsyncMock(return_value=None)
                
                event = UserLeveledUpEvent(
                    user_id=sample_user_entity.id,
                    old_level=level - 1,
                    new_level=level,
                    total_xp=XpPoints(level * 1000)
                )
                
                await achievement_handler.handle(event)
                
                # Assert achievement was created
                mock_repo.update.assert_called_once()
                updated_user = mock_repo.update.call_args[0][1]
                assert len(updated_user.achievements) == 1
                assert updated_user.achievements[0].name == f"Level {level} Achieved"
                assert f"level {level}" in updated_user.achievements[0].description.lower()
    
    @pytest.mark.asyncio
    async def test_no_achievement_for_non_milestone_levels(
        self, 
        sample_user_entity, 
        achievement_handler
    ):
        """Test that no achievement is created for non-milestone levels (odd levels)"""
        odd_levels = [1, 3, 5, 7, 9]
        
        for level in odd_levels:
            sample_user_entity.achievements = []
            
            with patch.object(achievement_handler, 'user_repo') as mock_repo:
                mock_repo.find_by_id = AsyncMock(return_value=sample_user_entity)
                mock_repo.update = AsyncMock(return_value=None)
                
                event = UserLeveledUpEvent(
                    user_id=sample_user_entity.id,
                    old_level=level - 1,
                    new_level=level,
                    total_xp=XpPoints(level * 1000)
                )
                
                await achievement_handler.handle(event)
                
                # Assert no update was called (no achievement created)
                mock_repo.find_by_id.assert_called_once()
                mock_repo.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_complete_integration_flow_dialogue_to_achievement(
        self, 
        sample_user_entity, 
        sample_user_dto, 
        sample_dialogue, 
        sample_practice_result,
        event_dispatcher,
        achievement_handler
    ):
        """Test the complete integration flow from dialogue practice to achievement creation"""
        # Register handler with the REAL global dispatcher
        from app.core.common.domain.events.event_dispatcher import event_dispatcher as real_dispatcher
        real_dispatcher.register_handler(achievement_handler)
        
        try:
            # Shared mock repo
            mock_repo = MagicMock()
            mock_repo.find_by_id = AsyncMock(return_value=sample_user_entity)
            mock_repo.update = AsyncMock(return_value=None)
            
            # Patch UserMongoRepository where it's used
            with patch('app.core.users.application.event_handlers.achievement_handler.UserMongoRepository', return_value=mock_repo), \
                 patch('app.business.user_bo.UserMongoRepository', return_value=mock_repo), \
                 patch('app.core.common.domain.events.event_dispatcher.event_dispatcher', real_dispatcher):
                
                # Ensure AchievementHandler instance uses our mock repo
                achievement_handler.user_repo = mock_repo
                
                # Ensure UserBusiness uses the mocked repo
                UserBusiness.user_repo = mock_repo
                
                # Mock other dependencies
                with patch.object(DialogueBusiness, 'get_dialogue') as mock_get_dialogue, \
                     patch.object(DialogueBusiness, 'dialogue_practice_history_repo') as mock_history_repo, \
                     patch.object(UserBusiness, 'update_progress') as mock_update_progress, \
                     patch('app.integration.audio_processor.AudioProcessor.client') as mock_audio:
                    
                    # Setup other mocks
                    mock_get_dialogue.side_effect = AsyncMock(return_value=sample_dialogue)
                    mock_history_repo.create = AsyncMock(return_value=None)
                    
                    # Manual side effect for update_progress to simulate level up
                    async def manual_update_progress(user_id, result):
                        print(f"DEBUG: manual_update_progress starting for user {user_id}, current_xp={sample_user_entity.progress.xp_points.value}")
                        sample_user_entity.update_progress(result.pronunciation_score, result.fluency_score, result.xp_earned)
                        print(f"DEBUG: manual_update_progress after update, new_xp={sample_user_entity.progress.xp_points.value}, new_level={sample_user_entity.progress.level}")
                        await mock_repo.update(user_id, sample_user_entity)
                        await UserBusiness._publish_user_events(sample_user_entity)
                        return sample_user_entity
                    
                    mock_update_progress.side_effect = manual_update_progress
                    
                    # Mock audio processing
                    mock_transcription = MagicMock()
                    mock_transcription.words = [{'confidence': 0.85, 'start_time': 0.0, 'end_time': 1.0}]
                    mock_transcription.transcribed_text = "Hello world"
                    mock_audio.process_audio_transcript = AsyncMock(return_value=mock_transcription)
                    
                    # Act - Process dialogue practice
                    audio_data = b"fake_audio_data"
                    result = await DialogueBusiness.proccess_practice_dialogue(
                        dialogue_id=sample_dialogue.id,
                        audio_data=audio_data,
                        user=sample_user_dto
                    )
                    
                    # Assert - Verify the flow worked
                    assert result is not None
                    
                    # Verify user repository update was called
                    # It should be called at least twice: 
                    # 1. By manual_update_progress
                    # 2. By AchievementHandler.handle (since user levels up to 2)
                    assert mock_repo.update.call_count >= 2
                    
                    # Verify achievement was created
                    updated_user = None
                    for call in mock_repo.update.call_args_list:
                        user = call[0][1]
                        if len(user.achievements) > 0:
                            updated_user = user
                            break
                    
                    assert updated_user is not None
                    assert updated_user.achievements[0].name == "Level 2 Achieved"
        finally:
            real_dispatcher.unregister_handler(achievement_handler)

    @pytest.mark.asyncio
    async def test_error_handling_user_not_found(
        self, 
        achievement_handler
    ):
        """Test error handling when user is not found during achievement creation"""
        with patch.object(achievement_handler, 'user_repo') as mock_repo:
            mock_repo.find_by_id = AsyncMock(return_value=None)
            mock_repo.update = AsyncMock(return_value=None)
            
            event = UserLeveledUpEvent(
                user_id=Uuid(),
                old_level=1,
                new_level=2,
                total_xp=XpPoints(1200)
            )
            
            # Should not raise exception, but log error
            await achievement_handler.handle(event)
            
            # Assert find was called but update was not
            mock_repo.find_by_id.assert_called_once()
            mock_repo.update.assert_not_called()

    # MEDIUM PRIORITY TESTS
    
    @pytest.mark.asyncio
    async def test_user_entity_updated_with_new_achievement(
        self, 
        sample_user_entity, 
        achievement_handler
    ):
        """Test that user entity is properly updated with new achievement"""
        initial_achievement_count = len(sample_user_entity.achievements)
        
        with patch.object(achievement_handler, 'user_repo') as mock_repo:
            mock_repo.find_by_id = AsyncMock(return_value=sample_user_entity)
            mock_repo.update = AsyncMock(return_value=None)
            
            event = UserLeveledUpEvent(
                user_id=sample_user_entity.id,
                old_level=1,
                new_level=2,
                total_xp=XpPoints(1200)
            )
            
            await achievement_handler.handle(event)
            
            # Verify the user entity was updated correctly
            update_call = mock_repo.update.call_args
            updated_user_id = update_call[0][0]
            updated_user_entity = update_call[0][1]
            
            assert updated_user_id == str(sample_user_entity.id)
            assert len(updated_user_entity.achievements) == initial_achievement_count + 1
            
            # Verify achievement properties
            new_achievement = updated_user_entity.achievements[-1]
            assert new_achievement.name == "Level 2 Achieved"
            assert "level 2" in new_achievement.description.lower()
            assert new_achievement.earned_at == event.occurred_at
            assert isinstance(new_achievement.id, Uuid)
    
    @pytest.mark.asyncio
    async def test_event_publishing_with_mocked_dependencies(self):
        """Test event publishing and handling with mocked dependencies"""
        dispatcher = EventDispatcher()
        
        # Create mock handler that tracks calls
        mock_handler = AsyncMock()
        mock_handler.event_type = "user.leveled_up"
        
        dispatcher.register_handler(mock_handler)
        
        event = UserLeveledUpEvent(
            user_id=Uuid(),
            old_level=3,
            new_level=4,
            total_xp=XpPoints(2500)
        )
        
        await dispatcher.publish(event)
        
        # Verify handler was called
        mock_handler.handle.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_xp_calculation_and_level_progression(self):
        """Test XP calculation and level progression logic"""
        user = UserEntity(
            email=Email("test@example.com"),
            name="Test User",
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
            progress=UserProgress(level=1, xp_points=XpPoints(0))
        )
        
        # Test level progression for multiple levels
        test_cases = [
            (500, 1),    # Not enough for level 2
            (1000, 2),   # Exactly level 2
            (1500, 2),   # Still level 2
            (2200, 3),   # Level 3 (1000 + 1200)
            (3640, 4),   # Level 4 (1000 + 1200 + 1440)
        ]
        
        for xp_to_add, expected_level in test_cases:
            user.progress.xp_points = XpPoints(0)  # Reset
            user.progress.level = 1
            user._uncommitted_events = []
            
            # Calculate XP needed to reach target
            current_xp = 0
            while current_xp < xp_to_add:
                remaining = min(300, xp_to_add - current_xp)
                user.update_progress(0.8, 0.7, remaining)
                current_xp += remaining
            
            assert user.progress.level == expected_level
            
            # Check if event was raised for level ups
            events = user.get_uncommitted_events()
            if expected_level > 1:
                assert len(events) >= 1
                assert all(isinstance(e, UserLeveledUpEvent) for e in events)
            else:
                assert len(events) == 0
    
    @pytest.mark.asyncio
    async def test_events_marked_as_committed_after_processing(
        self, 
        sample_user_entity
    ):
        """Test that events are marked as committed after processing"""
        # Trigger a level up to create events
        sample_user_entity.update_progress(0.9, 0.8, 300)
        
        # Verify events exist
        events = sample_user_entity.get_uncommitted_events()
        assert len(events) > 0
        
        # Simulate event processing and commitment
        with patch.object(UserBusiness, 'user_repo') as mock_repo:
            mock_repo.find_by_id = AsyncMock(return_value=sample_user_entity)
            mock_repo.update = AsyncMock(return_value=None)
            
            with patch('app.core.common.domain.events.event_dispatcher.event_dispatcher') as mock_dispatcher:
                mock_dispatcher.publish_all = AsyncMock(return_value=None)
                
                # Call the method that should commit events
                await UserBusiness._publish_user_events(sample_user_entity)
                
                # Verify events were published and committed
                mock_dispatcher.publish_all.assert_called_once_with(events)
                
                # Events should be cleared after commitment
                remaining_events = sample_user_entity.get_uncommitted_events()
                assert len(remaining_events) == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_level_ups(
        self, 
        sample_user_entity, 
        achievement_handler
    ):
        """Test concurrent level-ups (if user gains multiple levels at once)"""
        # Set up user close to level 1
        sample_user_entity.progress.level = 1
        sample_user_entity.progress.xp_points = XpPoints(800)
        
        # Give massive XP to trigger multiple level ups
        sample_user_entity.update_progress(0.95, 0.90, 5000)  # Should trigger multiple levels
        
        # Get all level up events
        events = sample_user_entity.get_uncommitted_events()
        level_up_events = [e for e in events if isinstance(e, UserLeveledUpEvent)]
        
        # Should have multiple level up events
        assert len(level_up_events) >= 2
        
        # Test that achievement handler processes each event correctly
        with patch.object(achievement_handler, 'user_repo') as mock_repo:
            mock_repo.find_by_id = AsyncMock(return_value=sample_user_entity)
            mock_repo.update = AsyncMock(return_value=None)
            
            achievements_created = 0
            for event in level_up_events:
                # Reset achievements to simulate fresh state
                sample_user_entity.achievements = []
                
                await achievement_handler.handle(event)
                
                # Count achievements created for even levels
                if event.new_level % 2 == 0:
                    achievements_created += 1
                    mock_repo.update.assert_called()
                    updated_user = mock_repo.update.call_args[0][1]
                    assert len(updated_user.achievements) == 1
                
                mock_repo.reset_mock()
            
            # Verify that achievements were created for the appropriate levels
            assert achievements_created > 0
    
    @pytest.mark.asyncio
    async def test_achievement_handler_error_handling_with_repository_failure(
        self, 
        sample_user_entity, 
        achievement_handler
    ):
        """Test error handling when repository operations fail"""
        with patch.object(achievement_handler, 'user_repo') as mock_repo:
            # Simulate repository failure
            mock_repo.find_by_id = AsyncMock(return_value=sample_user_entity)
            mock_repo.update = AsyncMock(side_effect=Exception("Database connection failed"))
            
            event = UserLeveledUpEvent(
                user_id=sample_user_entity.id,
                old_level=1,
                new_level=2,
                total_xp=XpPoints(1200)
            )
            
            # Should raise the exception
            with pytest.raises(Exception, match="Database connection failed"):
                await achievement_handler.handle(event)
            
            # Verify find was called but update failed
            mock_repo.find_by_id.assert_called_once()
            mock_repo.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_achievement_properties_validation(
        self, 
        sample_user_entity, 
        achievement_handler
    ):
        """Test that created achievements have correct properties"""
        with patch.object(achievement_handler, 'user_repo') as mock_repo:
            mock_repo.find_by_id = AsyncMock(return_value=sample_user_entity)
            mock_repo.update = AsyncMock(return_value=None)
            
            event_time = datetime.now(timezone.utc)
            event = UserLeveledUpEvent(
                user_id=sample_user_entity.id,
                old_level=3,
                new_level=4,
                total_xp=XpPoints(2500),
                occurred_at=event_time
            )
            
            await achievement_handler.handle(event)
            
            # Get the created achievement
            updated_user = mock_repo.update.call_args[0][1]
            achievement = updated_user.achievements[-1]
            
            # Validate achievement properties
            assert achievement.name == "Level 4 Achieved"
            assert "level 4" in achievement.description.lower()
            assert "congratulations" in achievement.description.lower()
            assert achievement.earned_at == event_time
            assert isinstance(achievement.id, Uuid)
            assert str(achievement.id)  # Should be valid UUID string
