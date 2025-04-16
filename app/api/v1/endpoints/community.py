
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.community_service import CommunityService
from app.models.user import User

router = APIRouter()
community_service = CommunityService()

@router.get("/insights/health")
async def get_community_health_insights(
    metric: str,
    timeframe: str = "week",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await community_service.get_health_insights(metric, timeframe)

@router.get("/insights/goals")
async def get_community_goals(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await community_service.get_popular_goals(category)

@router.get("/insights/trends")
async def get_community_trends(
    category: str,
    timeframe: str = "month",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await community_service.analyze_trends(category, timeframe)
