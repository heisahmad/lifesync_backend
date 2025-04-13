
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.services.notification_service import NotificationService

router = APIRouter()

@router.get("/")
async def get_notifications(
    unread_only: bool = False,
    current_user = Depends(get_current_user)
):
    notifications = await NotificationService.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only
    )
    return notifications

@router.post("/{notification_index}/read")
async def mark_notification_read(
    notification_index: int,
    current_user = Depends(get_current_user)
):
    await NotificationService.mark_notification_as_read(
        user_id=current_user.id,
        notification_index=notification_index
    )
    return {"status": "success"}
