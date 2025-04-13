
from datetime import datetime
from typing import Optional, Dict
from app.core.config import settings
import httpx
import redis

class NotificationService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)
        
    async def create_notification(
        self,
        user_id: int,
        notification_type: str,
        message: str,
        priority: str = "normal",
        metadata: Optional[Dict] = None
    ):
        notification = {
            "user_id": user_id,
            "type": notification_type,
            "message": message,
            "priority": priority,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "read": False
        }
        
        # Store in Redis for quick access
        notification_key = f"notification:{user_id}:{datetime.utcnow().timestamp()}"
        self.redis_client.hmset(notification_key, notification)
        
        # Set expiration for 30 days
        self.redis_client.expire(notification_key, 60 * 60 * 24 * 30)
        
        # If high priority, send immediate push notification
        if priority == "high":
            await self._send_push_notification(user_id, message)
            
    async def get_user_notifications(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0,
        unread_only: bool = False
    ) -> list:
        pattern = f"notification:{user_id}:*"
        notifications = []
        
        for key in self.redis_client.scan_iter(match=pattern):
            notification = self.redis_client.hgetall(key)
            if unread_only and notification.get("read", "false") == "true":
                continue
            notifications.append(notification)
            
        # Sort by created_at
        notifications.sort(key=lambda x: x.get("created_at"), reverse=True)
        return notifications[offset:offset + limit]
        
    async def mark_as_read(self, user_id: int, notification_ids: list):
        for notification_id in notification_ids:
            key = f"notification:{user_id}:{notification_id}"
            self.redis_client.hset(key, "read", "true")
            
    async def _send_push_notification(self, user_id: int, message: str):
        # Implementation for push notification service (e.g., Firebase)
        pass
