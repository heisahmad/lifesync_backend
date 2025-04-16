from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.api.deps import get_db, get_current_user
from app.models.goal import Goal, Milestone, ProgressLog
from app.models.gamification import UserProfile, Badge, UserBadge
from app.services.gamification_service import GamificationService

router = APIRouter()
gamification_service = GamificationService()

@router.post("/goals")
async def create_goal(
    goal_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    goal = Goal(user_id=current_user.id, **goal_data)
    db.add(goal)
    db.commit()
    return goal

@router.post("/goals/{goal_id}/progress")
async def log_progress(
    goal_id: int,
    progress_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Log progress
    progress = ProgressLog(goal_id=goal_id, **progress_data)
    db.add(progress)
    
    # Update goal progress
    goal.current_value = progress_data["value"]
    if goal.current_value >= goal.target_value:
        goal.completed = True
        
    db.commit()
    
    # Award XP and check achievements
    await gamification_service.process_progress(db, current_user.id, goal)
    return {"message": "Progress logged successfully"}

@router.get("/goals")
async def get_goals(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return db.query(Goal).filter(Goal.user_id == current_user.id).all()

@router.get("/profile")
async def get_profile(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()
    return profile

@router.get("/badges")
async def get_badges(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()
    return profile.badges if profile else []
