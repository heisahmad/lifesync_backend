
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base

class SmartDevice(Base):
    __tablename__ = "smart_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    device_type = Column(String(50))  # thermostat, light, switch, etc
    webhook_url = Column(String(500))
    webhook_secret = Column(String(100))
    config = Column(JSON)  # Store device-specific configuration
    last_state = Column(JSON)  # Store last known device state
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
