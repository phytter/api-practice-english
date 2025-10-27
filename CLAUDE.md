# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
uvicorn app.main:app --reload
```
The application will be available at `http://127.0.0.1:8000`.

### Running Tests
```bash
pytest
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

For development dependencies:
```bash
pip install -r requirements/develop.txt
```

## Architecture Overview

This is a FastAPI application for practicing English through movie dialogues, implementing Domain-Driven Design (DDD) principles with a clean architecture approach.

### Core Architecture Layers

**Domain Layer** (`app/core/*/domain/`):
- Contains entities, value objects, and repository interfaces
- Pure domain logic without external dependencies
- Each bounded context (dialogues, movies, users) has its own domain model

**Application Layer** (`app/core/*/application/`):
- DTOs, mappers, and application services
- Orchestrates domain operations and handles use cases

**Infrastructure Layer** (`app/core/*/infra/`):
- Database repositories implementing domain interfaces
- MongoDB-specific implementations

**Business Layer** (`app/business/`):
- Legacy business objects that orchestrate operations
- Being refactored towards DDD patterns

**HTTP Layer** (`app/http/`):
- REST API endpoints in `app/http/rest/v1/`
- FastAPI configuration and routing

### Key Design Patterns

**Value Objects**: Located in `app/core/common/domain/value_objects/`
- `Uuid` for entity identifiers
- `Email` for email validation
- `Score` and `XpPoints` for gaming elements

**Repository Pattern**: Each domain has repository interfaces in domain layer and MongoDB implementations in infrastructure layer.

**Factory Methods**: Entities use factory methods for creation with proper validation.

### Environment Configuration

The application uses Pydantic Settings (`app/core/config.py`) with environment variables:
- `SECRET_KEY`: JWT secret
- `MONGODB_URL`: MongoDB connection string  
- `GOOGLE_CLIENT_ID/SECRET`: OAuth credentials
- `OPENSUBTITLES_API_KEY`: External API key

### Testing Setup

- Uses pytest with async support
- Test files in `tests/` directory
- Mock objects available in `tests/mocks/`
- Configuration in `pytest.ini`

### External Integrations

- **Google Cloud Speech**: Audio processing for pronunciation feedback
- **OpenSubtitles API**: Movie dialogue retrieval
- **MongoDB**: Primary database using Motor (async driver)

### Current State

The codebase is transitioning from a traditional business layer approach to full DDD implementation. The `app/business/` layer contains legacy code being refactored into proper domain models in `app/core/`.