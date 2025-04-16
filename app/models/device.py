from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(String(100), unique=True, nullable=False)
    device_type = Column(String(50))  # mobile, desktop, tablet, etc.
    last_sync = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SyncQueue(Base):
    __tablename__ = "sync_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), ForeignKey("devices.device_id"), nullable=False)
    data_type = Column(String(50))  # calendar, email, health, etc.
    payload = Column(String)  # JSON serialized data
    status = Column(String(20), default="pending")  # pending, synced, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    synced_at = Column(DateTime(timezone=True))
