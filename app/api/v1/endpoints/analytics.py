
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.data_integration_service import DataIntegrationService
from app.services.analytics_service import AnalyticsService
from app.services.health_service import HealthService  # Added import
from app.services.finance_service import FinanceService  # Added import
from app.models.user import User  # Added import

router = APIRouter()

health_service = HealthService()  # Added instance
finance_service = FinanceService()  # Added instance

@router.get("/insights")
async def get_insights(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get data from different services
    health_data = await health_service.get_health_data(current_user.id, start_date, end_date)
    finance_data = await finance_service.get_finance_data(current_user.id, start_date, end_date)
    
    # Normalize and combine data
    health_df = await DataIntegrationService.normalize_health_data(health_data)
    finance_df = await DataIntegrationService.normalize_finance_data(finance_data)
    combined_df = await DataIntegrationService.combine_data_sources(health_df, finance_df)
    
    # Perform analytics
    time_series_analysis = await AnalyticsService.analyze_time_series(combined_df, 'activity_level')
    correlations = await AnalyticsService.detect_correlations(combined_df)
    anomalies = await AnalyticsService.detect_anomalies(combined_df, 'spending')
    
    return {
        "time_series_analysis": time_series_analysis,
        "correlations": correlations,
        "anomalies": anomalies
    }
