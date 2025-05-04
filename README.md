# API Practice English

Welcome to **API Practice English**! 🎉

This application is an interactive tool to practice and improve your English skills through movie dialogues. You can search for dialogues, practice your pronunciation and fluency, and track your progress over time.

## Features

- **Search Dialogues**: Find movie dialogues using keywords or IMDb IDs.
- **Practice Dialogues**: Submit audio recordings to receive feedback on your pronunciation and fluency.
- **Practice History**: Track your progress and view your practice history.

## Prerequisites

Before you begin, make sure you have the following installed:

- Python 3.8+
- FastAPI
- FFmpeg (for audio processing)

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/phytter/api-practice-english.git
    cd api-practice-english
    ```

2. Install the dependencies using `pip`:

    ```bash
    pip install -r requirements.txt
    ```

3. Install FFmpeg:

    ```bash
    sudo apt-get install ffmpeg
    ```

4. Configure the necessary environment variables (e.g., `MONGO_URI`, `AUDIO_PROCESSOR_API_KEY`).

## Running the Application

To start the application, run the following command:

```bash
uvicorn app.main:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

## Running the Tests

To run the tests, use the command:

```bash
pytest
```

## Related Projects

- [App Practice English - Frontend for this application](https://github.com/phytter/app-practice-english)

- [Infrastructure Practice English - Infra as code for this application](https://github.com/phytter/infrastructure-practice-english)

## Next Steps

1. Complete DDD Implementation:
- Introduce proper Value Objects for concepts like email, score ranges ✅
- Implement Domain Events for important state changes (level up, achievement unlocked)
- Define Aggregates with clear boundaries and invariants
2. Improve Error Handling:
- Create domain-specific exceptions
- Implement a consistent error handling strategy across layers
3. Implement CQRS Pattern:
- Separate command (write) and query (read) responsibilities
- Optimize read models for UI requirements
4. Implement Domain Services:
- Move complex business logic that doesn't belong in entities to domain services
- Ensure business layer only orchestrates domain operations
5. Performance Optimizations:
- Add caching for frequently accessed data
- Optimize MongoDB queries with proper indexes
- Implement async dialog processing with microsservices
6. Add Comprehensive Testing:
- Unit tests for domain logic and validation rules
- Integration tests for repositories
7. Documentation Improvements:
- Document domain model with diagrams
- Add comprehensive API documentation
- Document architectural decisions

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

Enjoy practicing your English with movie dialogues! 🎬📚

### License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.