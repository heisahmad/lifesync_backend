from typing import Dict, Optional, List
from datetime import datetime
import json
from fastapi import WebSocket
from app.utils.redis_utils import redis_cache
from app.core.config import settings
import httpx

class NotificationService:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: int):
        self.active_connections[user_id].remove(websocket)
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]

    async def create_notification(
        self, 
        user_id: int, 
        notification_type: str, 
        message: str, 
        data: Optional[Dict] = None,
        priority: str = "normal"
    ):
        notification = {
            "user_id": user_id,
            "type": notification_type,
            "message": message,
            "data": data,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
            "read": False
        }

        # Store in Redis with TTL
        key = f"notification:{user_id}:{datetime.utcnow().timestamp()}"
        await redis_cache.set_json(key, notification)

        # Send real-time notification if user is connected
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(notification)
                except Exception:
                    await self.disconnect(connection, user_id)

        # Send push notification if enabled
        if priority == "high":
            await self._send_push_notification(user_id, message)

    async def get_user_notifications(
        self, 
        user_id: int, 
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict]:
        notifications = []
        pattern = f"notification:{user_id}:*"
        
        async for key in redis_cache.redis_client.scan_iter(match=pattern):
            notification = await redis_cache.get_json(key)
            if notification and (not unread_only or not notification["read"]):
                notifications.append(notification)

        return sorted(
            notifications, 
            key=lambda x: x["created_at"], 
            reverse=True
        )[:limit]

    async def mark_as_read(self, user_id: int, notification_ids: List[str]):
        for notification_id in notification_ids:
            key = f"notification:{user_id}:{notification_id}"
            notification = await redis_cache.get_json(key)
            if notification:
                notification["read"] = True
                await redis_cache.set_json(key, notification)

    async def _send_push_notification(self, user_id: int, message: str):
        # Implement push notification logic here
        # This could integrate with Firebase Cloud Messaging, OneSignal, etc.
        pass

    async def handle_webhook(self, source: str, payload: Dict) -> Dict:
        """Handle incoming webhooks from various services"""
        handlers = {
            "fitbit": self._handle_fitbit_webhook,
            "plaid": self._handle_plaid_webhook,
            "google": self._handle_google_webhook
        }

        if source not in handlers:
            raise ValueError(f"Unknown webhook source: {source}")

        return await handlers[source](payload)

    async def _handle_fitbit_webhook(self, payload: Dict) -> Dict:
        # Process Fitbit notifications (activity updates, sleep data, etc.)
        notification_type = payload.get("collectionType")
        user_id = payload.get("subscriptionId")  # This should map to your user_id

        if notification_type == "activities":
            await self.create_notification(
                user_id=user_id,
                notification_type="fitbit_activity",
                message="New activity data available",
                data=payload
            )

        return {"status": "processed"}

    async def _handle_plaid_webhook(self, payload: Dict) -> Dict:
        # Process Plaid notifications (transactions, balance updates, etc.)
        webhook_type = payload.get("webhook_type")
        user_id = payload.get("item_id")  # Map this to your user_id

        if webhook_type == "TRANSACTIONS":
            await self.create_notification(
                user_id=user_id,
                notification_type="plaid_transaction",
                message="New transactions detected",
                data=payload,
                priority="high"
            )

        return {"status": "processed"}

    async def _handle_google_webhook(self, payload: Dict) -> Dict:
        # Process Google notifications (calendar updates, email, etc.)
        notification_type = payload.get("type")
        user_id = payload.get("user_id")

        if notification_type == "calendar":
            await self.create_notification(
                user_id=user_id,
                notification_type="google_calendar",
                message="Calendar event update",
                data=payload
            )

        return {"status": "processed"}