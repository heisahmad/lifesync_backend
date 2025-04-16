
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Optional
from app.api.deps import get_db, get_current_user
from app.services.intelligence_service import IntelligenceService
from app.models.user import User

router = APIRouter()
intelligence_service = IntelligenceService()

@router.get("/behavior-patterns")
async def analyze_behavior_patterns(
    timeframe: str = "week",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await intelligence_service.analyze_behavior_patterns(current_user.id, timeframe)

@router.get("/burnout-risk")
async def detect_burnout_risk(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await intelligence_service.detect_burnout_risk(current_user.id)

@router.get("/mood-analysis") 
async def analyze_mood(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await intelligence_service.analyze_mood(current_user.id)

@router.post("/voice-command")
async def process_voice_command(
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await intelligence_service.process_voice_command(audio_file, current_user.id)
