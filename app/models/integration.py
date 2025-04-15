from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class Integration(Base):
    __tablename__ = "integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)  # e.g., "fitbit", "plaid", "google"
    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=True)
    credentials = Column(JSON, nullable=True)  # For storing JSON credentials
    is_active = Column(Boolean, default=True)
    expires_at = Column(Integer, nullable=True)  # Unix timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Add any service-specific fields here
    scopes = Column(String(1000), nullable=True)  # For OAuth scopes
    token_type = Column(String(50), nullable=True)