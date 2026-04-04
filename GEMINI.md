# API Practice English - Project Context

## Project Overview

**API Practice English** is an interactive application designed to help users practice and improve their English skills using movie dialogues. It allows users to search for dialogues, record their pronunciation, and receive feedback. The system tracks progress, manages user levels, and awards achievements.

## Architecture

The project follows **Clean Architecture** and **Domain-Driven Design (DDD)** principles, organizing code into layers to separate concerns and maintain independence from external frameworks and tools.

### Layered Structure

*   **`app/core/`**: The heart of the application. Contains the **Domain Layer**.
    *   **`common/`**: Shared domain concepts (Entities, Value Objects, Events).
    *   **`[module]/domain/`**: Module-specific domain logic (e.g., `users`, `dialogues`, `movies`).
*   **`app/business/`**: The **Application Layer** (Use Cases). Orchestrates domain objects to fulfill business requirements.
*   **`app/adapters/`**: Interface Adapters. Converts data between the domain and external formats (e.g., `google_audio_processor.py`).
*   **`app/infra/`**: Infrastructure Layer. Implements interfaces defined in the domain (e.g., database repositories).
*   **`app/http/`**: The Web Layer (FastAPI). Handles HTTP requests and routes them to the business layer.
*   **`app/integration/`**: External service integrations.

### DDD Patterns Used

*   **Entities**: Mutable objects with identity (e.g., `User`, `Dialogue`).
*   **Value Objects**: Immutable objects defined by their attributes (e.g., `Email`, `Score`, `XpPoints`).
*   **Domain Events**: Events triggered by state changes (e.g., `UserLeveledUpEvent`, `PracticeCompletedEvent`).
*   **Repositories**: Interfaces for accessing data, implemented in the infrastructure layer.
*   **Aggregates**: Clusters of domain objects treated as a single unit (implied structure).

## Technology Stack

*   **Language**: Python 3.8+
*   **Web Framework**: FastAPI (with Uvicorn)
*   **Database**: MongoDB (using Motor for async and PyMongo)
*   **Audio Processing**: FFmpeg, PyDub, Google Cloud Speech
*   **Testing**: Pytest
*   **Other**: Aiohttp, Pydantic, Python-Jose

## Setup & Usage

### Prerequisites
*   Python 3.8+
*   FFmpeg
*   MongoDB Instance

### Installation
1.  Install dependencies: `pip install -r requirements.txt`
2.  Set up environment variables (see `.env.example`).

### Running the Application
```bash
uvicorn app.main:app --reload
```
Access docs at: `http://127.0.0.1:8000/api/docs`

### Running Tests
```bash
pytest
```

## Key Files & Directories

*   `app/main.py`: Application entry point.
*   `app/http/config.py`: FastAPI configuration (middleware, routes, startup/shutdown events).
*   `app/core/common/domain/events/event_setup.py`: Central registration for domain event handlers.
*   `docs/DOMAIN_EVENTS.md`: Detailed documentation of the event-driven architecture.
*   `requirements/base.txt`: Core project dependencies.

## Development Guidelines

*   **Domain First**: Implement core logic in `app/core` before adding external dependencies.
*   **Event-Driven**: Use `DomainEvent` for side effects (e.g., achievements, analytics).
*   **Separation of Concerns**: Keep business logic out of HTTP handlers (`app/http/rest`) and database models (`app/infra`).
*   **Testing**: Write tests for domain logic and integration tests for repositories.

## Future Roadmap

*   **DDD Completeness**: Define clearer Aggregate boundaries and invariants.
*   **CQRS**: Separate Command and Query models for performance.
*   **Async Processing**: Move event handling to background queues (e.g., Celery/RabbitMQ).
*   **Event Store**: Persist events for audit trails and replay capabilities.
