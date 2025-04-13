
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.financial_service import FinancialService
from app.services.notification_service import NotificationService
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/analysis")
async def get_financial_analysis(
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Get user's Plaid integration
    integration = db.query(Integration).filter(
        Integration.user_id == current_user.id,
        Integration.type == "plaid",
        Integration.is_active == True
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Plaid integration not found")
        
    financial_service = FinancialService(access_token=integration.access_token)
    
    # Default to last 30 days if no dates provided
    start_date = start_date or (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = end_date or datetime.now().strftime('%Y-%m-%d')
    
    # Fetch and analyze transactions
    transactions = await financial_service.get_transactions(start_date, end_date)
    spending_analysis = await financial_service.analyze_spending(transactions)
    recommendations = await financial_service.generate_financial_recommendations(spending_analysis)
    
    # Create notification for high spending categories
    for category, amount in spending_analysis["spending_by_category"].items():
        if amount > 1000:
            await NotificationService.create_notification(
                user_id=current_user.id,
                notification_type="high_spending_alert",
                message=f"High spending detected in {category}",
                data={"category": category, "amount": amount}
            )
    
    return {
        "spending_analysis": spending_analysis,
        "recommendations": recommendations
    }
