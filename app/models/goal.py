from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Goal(Base):
    __tablename__ = "goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(1000))
    category = Column(String(50))  # health, finance, personal, etc.
    target_value = Column(Float)
    current_value = Column(Float, default=0)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True))
    completed = Column(Boolean, default=False)
    milestones = relationship("Milestone", back_populates="goal")
    progress_logs = relationship("ProgressLog", back_populates="goal")

class Milestone(Base):
    __tablename__ = "milestones"
    
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    title = Column(String(200), nullable=False)
    target_value = Column(Float)
    completed = Column(Boolean, default=False)
    goal = relationship("Goal", back_populates="milestones")

class ProgressLog(Base):
    __tablename__ = "progress_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    value = Column(Float)
    notes = Column(String(500))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    goal = relationship("Goal", back_populates="progress_logs")
