from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "English Practice Platform"

    APP_DEBUG: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
