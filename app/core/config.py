from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "English Practice Platform"
    APP_DEBUG: bool = False

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 21600  # 15 days

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "english_practice_db"

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    
    # OpenSubtitles
    OPENSUBTITLES_API_KEY: str
    OPENSUBTITLES_API_URL: str = "https://api.opensubtitles.com/api/v1"

    # Movie Service
    MOVIE_SERVICE: str = "OpenSubTitles"

    class Config:
        env_file = ".env"

settings = Settings()
