# Domain Events Implementation

This document describes the domain events architecture implemented in the API Practice English application.

## Overview

Domain Events are a pattern that helps decouple domain logic by allowing entities to raise events when important state changes occur. These events are then handled by separate event handlers, enabling cross-cutting concerns like notifications, analytics, and complex business workflows.

## Architecture

### Core Components

```
Domain Entity → Raises Events → Event Dispatcher → Event Handlers → Side Effects
```

#### 1. Domain Events
- **Base Class**: [`DomainEvent`](../app/core/common/domain/events/domain_event.py)
- **Purpose**: Abstract base for all domain events
- **Properties**: `event_id`, `aggregate_id`, `occurred_at`, `event_type`

#### 1.1. Integration Events
- **Base Class**: [`IntegrationEvent`](../app/core/common/domain/events/integration_event.py) (extends DomainEvent)
- **Purpose**: Events that cross bounded context boundaries
- **Usage**: When multiple domains need to react to the same event
- **Example**: `PracticeCompletedEvent` affects Users, Dialogues, and Analytics domains

#### 2. Event Dispatcher
- **Class**: [`EventDispatcher`](../app/core/common/domain/events/event_dispatcher.py)
- **Purpose**: Routes events to registered handlers
- **Type**: In-memory, synchronous processing
- **Global Instance**: `event_dispatcher` in [`event_dispatcher.py`](../app/core/common/domain/events/event_dispatcher.py)

#### 3. Event Handlers
- **Base Class**: [`EventHandler`](../app/core/common/domain/events/event_handler.py)
- **Purpose**: Process specific types of domain events
- **Registration**: Automatic during application startup

#### 4. Enhanced Entities
- **Base Class**: [`Entity`](../app/core/common/domain/entity.py) with events support
- **Methods**: `raise_event()`, `get_uncommitted_events()`, `mark_events_as_committed()`

## Implemented Events

### 1. UserLeveledUpEvent

**Trigger**: When a user's level increases during progress update
**Location**: [`user_leveled_up_event.py`](../app/core/users/domain/events/user_leveled_up_event.py)

```python
UserLeveledUpEvent(
    user_id=Uuid("user-123"),
    old_level=1,
    new_level=2,
    total_xp=XpPoints(1500)
)
```

**Data**:
- `user_id`: User who leveled up
- `old_level`: Previous level
- `new_level`: Current level
- `levels_gained`: Number of levels gained
- `total_xp`: Total XP after level up

### 2. PracticeCompletedEvent (Integration Event)

**Type**: Integration Event (crosses domain boundaries)
**Trigger**: When a user completes a dialogue practice session
**Location**: [`practice_completed_event.py`](../app/core/dialogues/domain/events/practice_completed_event.py)

**Why Integration Event?**
This event carries information needed by multiple bounded contexts:
- **Users Domain**: Updates user progress, levels, achievements
- **Dialogues Domain**: Records practice history
- **Analytics Domain**: Tracks performance metrics
- **Notifications Domain**: May trigger congratulatory messages

```python
PracticeCompletedEvent(
    user_id=Uuid("user-123"),
    dialogue_id=Uuid("dialogue-456"),
    pronunciation_score=Score(0.85),
    fluency_score=Score(0.78),
    xp_earned=XpPoints(150),
    practice_duration_seconds=45.5,
    difficulty_level=3
)
```

**Data**:
- `user_id`: User who completed practice
- `dialogue_id`: Practiced dialogue
- `pronunciation_score`: Score (0-1)
- `fluency_score`: Score (0-1)
- `average_score`: Calculated average
- `xp_earned`: XP awarded
- `practice_duration_seconds`: Practice time
- `difficulty_level`: Dialogue difficulty (1-5)

## Event Handlers

### 1. AchievementHandler

**Purpose**: Creates achievements when users level up
**Location**: [`achievement_handler.py`](../app/core/users/application/event_handlers/achievement_handler.py)
**Handles**: `user.leveled_up` events

**Logic**:
- Creates achievement for every 2nd level (2, 4, 6, etc.)
- Adds achievement to user's collection
- Persists updated user entity

### 2. AnalyticsHandler

**Purpose**: Logs practice analytics data
**Location**: [`analytics_handler.py`](../app/core/users/application/event_handlers/analytics_handler.py)
**Handles**: `dialogue.practice_completed` events

**Logic**:
- Logs structured practice data
- Future: Send to analytics services, update leaderboards, etc.

## Usage Examples

### Raising Events in Entities

```python
class UserEntity(Entity):
    def update_progress(self, pronunciation_score: float, fluency_score: float, xp_earned: int):
        old_level = self.progress.level
        self.progress.update_with_practice_result(pronunciation_score, fluency_score, xp_earned)
        
        # Raise domain event if level changed
        if self.progress.level > old_level:
            event = UserLeveledUpEvent(
                user_id=self.id,
                old_level=old_level,
                new_level=self.progress.level,
                total_xp=self.progress.xp_points
            )
            self.raise_event(event)
```

### Publishing Events in Business Layer

```python
# In DialogueBusiness.proccess_practice_dialogue()
user_entity = await UserBusiness.update_progress(user.id, result)

# Publish practice completed event
practice_event = PracticeCompletedEvent(...)
await event_dispatcher.publish(practice_event)

# Publish user events (like level up)
user_events = user_entity.get_uncommitted_events()
await event_dispatcher.publish_all(user_events)
user_entity.mark_events_as_committed()
```

### Creating Custom Event Handlers

```python
class NotificationHandler(EventHandler):
    @property
    def event_type(self) -> str:
        return "user.leveled_up"
    
    async def handle(self, event: UserLeveledUpEvent) -> None:
        # Send push notification
        await notification_service.send(
            user_id=event.user_id,
            message=f"Congratulations! You reached level {event.new_level}!"
        )
```

## Configuration

### Application Startup

Event handlers are registered during application startup in [`event_setup.py`](../app/core/common/domain/events/event_setup.py):

```python
def setup_event_handlers():
    achievement_handler = AchievementHandler()
    event_dispatcher.register_handler(achievement_handler)
    
    analytics_handler = AnalyticsHandler()
    event_dispatcher.register_handler(analytics_handler)
```

Called from [`app/http/config.py`](../app/http/config.py) in `startup_event()`.

## Testing

Comprehensive tests are available in [`tests/test_domain_events.py`](../tests/test_domain_events.py):

- Event creation and properties
- Event dispatcher functionality
- Entity event raising
- Handler registration and execution
- Event serialization

Run tests:
```bash
pytest tests/test_domain_events.py -v
```

## Event Types Classification

### Domain Events vs Integration Events

**Domain Events** (Internal to one bounded context):
- `UserLeveledUpEvent`: Pure user domain event
- Handled within the same bounded context
- Fast, synchronous processing

**Integration Events** (Cross bounded context boundaries):
- `PracticeCompletedEvent`: Affects multiple domains
- Contains rich information for cross-domain coordination
- May require more complex error handling and eventual consistency

## Benefits Achieved

### 1. **Decoupling**
- Achievement creation is no longer embedded in `UserEntity`
- Practice analytics separated from core business logic
- Cross-cutting concerns handled independently
- **Clear distinction** between domain and integration events

### 2. **Extensibility**
- Easy to add new event handlers (notifications, external APIs)
- New events can be added without changing existing code
- Handler failure doesn't break main flow

### 3. **Testability**
- Events can be tested in isolation
- Handlers can be mocked for business logic tests
- Clear separation of responsibilities

### 4. **Auditability**
- All events are logged with timestamps
- Event data provides audit trail of important changes
- Future: Events can be persisted for replay/debugging

## Future Enhancements

### Phase 2 - Additional Events
- `ScoreMilestoneReachedEvent` - High scores achieved
- `LongPracticeStreakEvent` - Consecutive practice days
- `PersonalBestScoreEvent` - New personal records

### Phase 3 - Advanced Features
- **Event Store**: Persist events for replay and auditing
- **Async Processing**: Move to queue-based event processing
- **External Integrations**: Webhooks, analytics services, notifications
- **Event Sourcing**: Build projections from event streams

### Phase 4 - Production Features
- **Retry Logic**: Handle failed event processing
- **Dead Letter Queue**: Failed events for investigation
- **Event Monitoring**: Metrics and alerting
- **Event Versioning**: Handle schema evolution

## Performance Considerations

- **Current**: Synchronous, in-memory processing
- **Latency**: Sub-millisecond event processing
- **Memory**: Events cleared after processing
- **Failure Handling**: Errors logged, main flow continues

## Monitoring

Event processing is logged with structured data:
- Event publication: `INFO` level
- Handler execution: `DEBUG` level  
- Handler errors: `ERROR` level
- Analytics data: `INFO` level

Monitor logs for:
- Event processing failures
- Handler execution times
- Event frequency patterns