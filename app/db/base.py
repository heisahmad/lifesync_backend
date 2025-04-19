from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

# Always use SQLite for development
SQLALCHEMY_DATABASE_URL = "sqlite:///lifesync.db"

# Configure SQLite to support concurrent access
connect_args = {"check_same_thread": False}
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import all models here
from app.models.user import User
from app.models.integration import Integration
from app.models.goal import Goal, Milestone, ProgressLog
from app.models.gamification import UserProfile, Badge, UserBadge
from app.models.device import Device, SyncQueue
from app.models.smart_home import SmartDevice
from app.models.ar_data import ARLocation, ARObject

def create_tables():
    Base.metadata.create_all(bind=engine)