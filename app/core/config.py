
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LifeSync"
    
    # Database
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # External APIs
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    FITBIT_CLIENT_ID: Optional[str] = None
    FITBIT_CLIENT_SECRET: Optional[str] = None
    PLAID_CLIENT_ID: Optional[str] = None
    PLAID_CLIENT_SECRET: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
