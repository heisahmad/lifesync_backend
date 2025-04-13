from typing import Dict, Optional, List
from datetime import datetime
import redis
from app.core.config import settings

class NotificationService:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.REDIS_URL)

    async def create_notification(self, user_id: int, notification_type: str, message: str, data: Optional[Dict] = None):
        notification = {
            "user_id": user_id,
            "type": notification_type,
            "message": message,
            "data": data,
            "created_at": datetime.utcnow().isoformat(),
            "read": False
        }

        # Store in Redis with TTL of 7 days
        key = f"notification:{user_id}:{datetime.utcnow().timestamp()}"
        self.redis_client.setex(key, 604800, str(notification))

    async def get_user_notifications(self, user_id: int, unread_only: bool = False) -> List[Dict]:
        notifications = []
        pattern = f"notification:{user_id}:*"

        for key in self.redis_client.scan_iter(match=pattern):
            notification = eval(self.redis_client.get(key))
            if not unread_only or not notification["read"]:
                notifications.append(notification)

        return sorted(notifications, key=lambda x: x["created_at"], reverse=True)

    async def mark_as_read(self, user_id: int, notification_ids: List[str]):
        for notification_id in notification_ids:
            key = f"notification:{user_id}:{notification_id}"
            if self.redis_client.exists(key):
                notification = eval(self.redis_client.get(key))
                notification["read"] = True
                self.redis_client.setex(key, 604800, str(notification))