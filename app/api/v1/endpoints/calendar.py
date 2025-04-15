
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.google_calendar_service import GoogleCalendarService
from app.services.schedule_optimizer import ScheduleOptimizer
from app.services.fitbit_service import FitbitService  # Added import
from app.models.integration import Integration  # Added import
from app.models.user import User  # Added import
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/events")
async def get_calendar_events(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    integration = db.query(Integration).filter(
        Integration.user_id == current_user.id,
        Integration.type == "google",
        Integration.is_active == True
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Google integration not found")
        
    calendar_service = GoogleCalendarService(integration.credentials)
    events = await calendar_service.get_events(start_date, end_date)
    analysis = await calendar_service.analyze_calendar_density(events)
    
    return {
        "events": events,
        "analysis": analysis
    }

@router.get("/optimizer")
async def optimize_schedule(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    google_integration = db.query(Integration).filter(
        Integration.user_id == current_user.id,
        Integration.type == "google",
        Integration.is_active == True
    ).first()
    
    fitbit_integration = db.query(Integration).filter(
        Integration.user_id == current_user.id,
        Integration.type == "fitbit",
        Integration.is_active == True
    ).first()
    
    if not (google_integration and fitbit_integration):
        raise HTTPException(status_code=404, detail="Required integrations not found")
        
    calendar_service = GoogleCalendarService(google_integration.credentials)
    health_service = FitbitService(fitbit_integration.access_token)
    optimizer = ScheduleOptimizer(calendar_service, health_service)
    
    optimization_result = await optimizer.optimize_schedule(start_date, end_date)
    return optimization_result
