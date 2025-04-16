from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.services.gmail_service import GmailService
from app.models.integration import Integration
from typing import List

router = APIRouter()

@router.get("/messages")
async def get_messages(
    max_results: int = 100,
    label_ids: List[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    integration = db.query(Integration).filter(
        Integration.user_id == current_user.id,
        Integration.type == "google",
        Integration.is_active == True
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Google integration not found")
        
    gmail_service = GmailService(integration.credentials)
    return await gmail_service.get_emails(max_results, label_ids)

@router.post("/labels")
async def create_label(
    name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    integration = db.query(Integration).filter(
        Integration.user_id == current_user.id,
        Integration.type == "google",
        Integration.is_active == True
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Google integration not found")
        
    gmail_service = GmailService(integration.credentials)
    return await gmail_service.create_label(name)
