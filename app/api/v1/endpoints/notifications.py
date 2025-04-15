from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel  # Added import
from app.api.deps import get_current_user
from app.services.notification_service import NotificationService
from app.models.user import User  # Added import
from typing import List  # Added import

router = APIRouter()

class Notification(BaseModel):  # Added model
    id: int
    message: str
    read: bool

@router.get("/", response_model=List[Notification])  # Added response model
async def get_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user)  # Added type hint
):
    notifications = await NotificationService.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only
    )
    return notifications

@router.post("/{notification_index}/read")
async def mark_notification_read(
    notification_index: int,
    current_user: User = Depends(get_current_user)  # Added type hint
):
    await NotificationService.mark_notification_as_read(
        user_id=current_user.id,
        notification_index=notification_index
    )
    return {"status": "success"}