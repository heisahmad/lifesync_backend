from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.fitbit_service import FitbitService
from app.services.health_analysis_service import HealthAnalysisService
from app.models.integration import Integration  # Added import
from app.models.user import User  # Added import
from datetime import datetime, timedelta

router = APIRouter()
health_analysis_service = HealthAnalysisService()

@router.get("/analysis")
async def get_health_analysis(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get user's Fitbit integration
    integration = db.query(Integration).filter(
        Integration.user_id == current_user.id,
        Integration.type == "fitbit",
        Integration.is_active == True
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Fitbit integration not found")
        
    fitbit_service = FitbitService(
        access_token=integration.access_token,
        refresh_token=integration.refresh_token
    )
    
    # Fetch health data
    sleep_data = await fitbit_service.get_sleep_data(start_date, end_date)
    activity_data = await fitbit_service.get_activity_data(start_date, end_date)
    
    # Analyze data
    sleep_analysis = await health_analysis_service.analyze_sleep_patterns(sleep_data)
    activity_analysis = await health_analysis_service.analyze_activity_patterns(activity_data)
    
    # Generate recommendations
    recommendations = await health_analysis_service.generate_health_recommendations(
        sleep_analysis,
        activity_analysis
    )
    
    return {
        "sleep_analysis": sleep_analysis,
        "activity_analysis": activity_analysis,
        "recommendations": recommendations
    }