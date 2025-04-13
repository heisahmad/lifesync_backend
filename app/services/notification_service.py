
from typing import Dict, List
from app.utils.redis_utils import redis_client
import json

class NotificationService:
    @staticmethod
    async def create_notification(user_id: int, notification_type: str, message: str, data: Dict = None):
        notification = {
            "type": notification_type,
            "message": message,
            "data": data,
            "read": False,
            "created_at": datetime.now().isoformat()
        }
        
        notifications_key = f"user:{user_id}:notifications"
        redis_client.lpush(notifications_key, json.dumps(notification))
        redis_client.ltrim(notifications_key, 0, 99)  # Keep last 100 notifications
        
    @staticmethod
    async def get_user_notifications(user_id: int, unread_only: bool = False) -> List[Dict]:
        notifications_key = f"user:{user_id}:notifications"
        notifications = []
        
        for notification_json in redis_client.lrange(notifications_key, 0, -1):
            notification = json.loads(notification_json)
            if not unread_only or not notification["read"]:
                notifications.append(notification)
                
        return notifications
        
    @staticmethod
    async def mark_notification_as_read(user_id: int, notification_index: int):
        notifications_key = f"user:{user_id}:notifications"
        notification_json = redis_client.lindex(notifications_key, notification_index)
        
        if notification_json:
            notification = json.loads(notification_json)
            notification["read"] = True
            redis_client.lset(notifications_key, notification_index, json.dumps(notification))
