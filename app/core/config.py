from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LifeSync"
    API_PORT: int = 5000  # Changed default port to 5000
    
    # Security
    TOKEN_EXPIRY_HOURS: int = 24
    SECRET_KEY: str = "your-secret-key-here"  # Default for development
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Database
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    USE_SQLITE: bool = True  # Added flag to force SQLite usage
    
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

    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields from environment variables

settings = Settings()
