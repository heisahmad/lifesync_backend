
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_user
from app.services.analytics_service import AnalyticsService
from app.services.recommendation_service import RecommendationService
from app.services.health_analysis_service import HealthAnalysisService
from app.services.financial_service import FinancialService
from app.services.social_connection_service import SocialConnectionService

router = APIRouter()

@router.get("/daily")
async def get_daily_insights(
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    date = date or datetime.now().strftime('%Y-%m-%d')
    
    # Gather data from various services
    health_analysis = await HealthAnalysisService.analyze_activity_patterns(date)
    financial_analysis = await FinancialService(current_user.plaid_token).analyze_spending(date)
    social_analysis = await SocialConnectionService.analyze_communication_patterns(date)
    
    # Generate insights and recommendations
    recommendation_service = RecommendationService()
    recommendations = await recommendation_service.generate_rule_based_recommendations({
        'health': health_analysis,
        'finance': financial_analysis,
        'social': social_analysis
    })
    
    return {
        "date": date,
        "health_insights": health_analysis,
        "financial_insights": financial_analysis,
        "social_insights": social_analysis,
        "recommendations": recommendations
    }

@router.get("/weekly")
async def get_weekly_insights(
    start_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=7)).strftime('%Y-%m-%d')
    
    analytics_service = AnalyticsService()
    weekly_patterns = await analytics_service.analyze_time_series(start_date, end_date)
    correlations = await analytics_service.detect_correlations(start_date, end_date)
    
    return {
        "period": {
            "start": start_date,
            "end": end_date
        },
        "patterns": weekly_patterns,
        "correlations": correlations
    }

@router.get("/monthly")
async def get_monthly_insights(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if not month or not year:
        today = datetime.now()
        month = today.month
        year = today.year
        
    analytics_service = AnalyticsService()
    monthly_trends = await analytics_service.analyze_monthly_patterns(year, month)
    predictions = await analytics_service.generate_predictions(monthly_trends)
    
    return {
        "period": {
            "month": month,
            "year": year
        },
        "trends": monthly_trends,
        "predictions": predictions
    }

@router.get("/custom")
async def get_custom_insights(
    start_date: str,
    end_date: str,
    metrics: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    analytics_service = AnalyticsService()
    custom_analysis = await analytics_service.analyze_custom_period(
        start_date,
        end_date,
        metrics or ["health", "finance", "social", "productivity"]
    )
    
    return {
        "period": {
            "start": start_date,
            "end": end_date
        },
        "analysis": custom_analysis
    }
