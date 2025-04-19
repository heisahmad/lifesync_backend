from typing import Dict, Any, Optional, List
from datetime import datetime
from app.utils.redis_utils import redis_cache
from app.utils.logging_utils import logger
from app.models.user import User
from sqlalchemy.orm import Session

class UserPreferenceService:
    DEFAULT_PREFERENCES = {
        "notifications": {
            "email": True,
            "push": True,
            "web": True,
            "quiet_hours": {
                "enabled": False,
                "start": "22:00",
                "end": "07:00"
            }
        },
        "privacy": {
            "share_health_data": False,
            "share_location": False,
            "share_activity": False
        },
        "display": {
            "theme": "system",
            "language": "en",
            "timezone": "UTC"
        },
        "health": {
            "daily_step_goal": 10000,
            "sleep_goal_hours": 8,
            "workout_days": ["Mon", "Wed", "Fri"],
            "track_nutrition": True
        },
        "productivity": {
            "work_hours": {
                "start": "09:00",
                "end": "17:00"
            },
            "break_interval": 60,  # minutes
            "focus_mode": {
                "enabled": False,
                "duration": 25  # minutes
            }
        },
        "integrations": {
            "fitbit": {
                "sync_frequency": "hourly",
                "metrics": ["steps", "heart_rate", "sleep"]
            },
            "google_calendar": {
                "sync_frequency": "15min",
                "calendars": ["primary"]
            }
        }
    }

    @staticmethod
    async def get_preferences(user_id: int) -> Dict[str, Any]:
        """Get user preferences with defaults for missing values"""
        cache_key = f"preferences:{user_id}"
        preferences = await redis_cache.get_json(cache_key)
        
        if not preferences:
            preferences = UserPreferenceService.DEFAULT_PREFERENCES.copy()
            await redis_cache.set_json(cache_key, preferences)
        
        return preferences

    @staticmethod
    async def update_preferences(
        user_id: int,
        preferences: Dict[str, Any],
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update user preferences for specific category or entire preferences"""
        cache_key = f"preferences:{user_id}"
        current_preferences = await UserPreferenceService.get_preferences(user_id)
        
        try:
            if category:
                if category not in current_preferences:
                    raise ValueError(f"Invalid preference category: {category}")
                current_preferences[category].update(preferences)
            else:
                for key, value in preferences.items():
                    if key in current_preferences:
                        if isinstance(value, dict):
                            current_preferences[key].update(value)
                        else:
                            current_preferences[key] = value
                            
            await redis_cache.set_json(cache_key, current_preferences)
            
            # Log preference update
            logger.logger.info(
                "User preferences updated",
                extra={
                    "user_id": user_id,
                    "category": category,
                    "updated_fields": list(preferences.keys())
                }
            )
            
            return current_preferences
            
        except Exception as e:
            await logger.log_error(
                error=e,
                module="user_preference_service",
                function="update_preferences",
                user_id=user_id,
                extra_data={"category": category, "preferences": preferences}
            )
            raise

    @staticmethod
    async def reset_preferences(
        user_id: int,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reset preferences to defaults for specific category or all preferences"""
        if category:
            if category not in UserPreferenceService.DEFAULT_PREFERENCES:
                raise ValueError(f"Invalid preference category: {category}")
            
            current_preferences = await UserPreferenceService.get_preferences(user_id)
            current_preferences[category] = (
                UserPreferenceService.DEFAULT_PREFERENCES[category].copy()
            )
            
            await redis_cache.set_json(
                f"preferences:{user_id}",
                current_preferences
            )
            return current_preferences
        else:
            default_preferences = UserPreferenceService.DEFAULT_PREFERENCES.copy()
            await redis_cache.set_json(
                f"preferences:{user_id}",
                default_preferences
            )
            return default_preferences

    @staticmethod
    async def get_notification_settings(user_id: int) -> Dict[str, Any]:
        """Get user's notification preferences"""
        preferences = await UserPreferenceService.get_preferences(user_id)
        return preferences["notifications"]

    @staticmethod
    async def should_send_notification(user_id: int, notification_type: str) -> bool:
        """Check if notification should be sent based on user preferences"""
        preferences = await UserPreferenceService.get_preferences(user_id)
        notification_settings = preferences["notifications"]
        
        # Check quiet hours
        if notification_settings["quiet_hours"]["enabled"]:
            now = datetime.now().time()
            quiet_start = datetime.strptime(
                notification_settings["quiet_hours"]["start"],
                "%H:%M"
            ).time()
            quiet_end = datetime.strptime(
                notification_settings["quiet_hours"]["end"],
                "%H:%M"
            ).time()
            
            # Handle overnight quiet hours
            if quiet_start > quiet_end:
                if now >= quiet_start or now <= quiet_end:
                    return False
            else:
                if quiet_start <= now <= quiet_end:
                    return False
        
        # Check notification type settings
        return notification_settings.get(notification_type, True)

    @staticmethod
    async def get_integration_settings(
        user_id: int,
        integration_name: str
    ) -> Dict[str, Any]:
        """Get settings for specific integration"""
        preferences = await UserPreferenceService.get_preferences(user_id)
        if integration_name not in preferences["integrations"]:
            raise ValueError(f"Invalid integration name: {integration_name}")
        
        return preferences["integrations"][integration_name]

    @staticmethod
    async def update_integration_settings(
        user_id: int,
        integration_name: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update settings for specific integration"""
        preferences = await UserPreferenceService.get_preferences(user_id)
        
        if integration_name not in preferences["integrations"]:
            preferences["integrations"][integration_name] = {}
            
        preferences["integrations"][integration_name].update(settings)
        
        await redis_cache.set_json(f"preferences:{user_id}", preferences)
        return preferences["integrations"][integration_name]

    @staticmethod
    async def get_health_goals(user_id: int) -> Dict[str, Any]:
        """Get user's health-related goals and preferences"""
        preferences = await UserPreferenceService.get_preferences(user_id)
        return preferences["health"]

    @staticmethod
    async def get_work_schedule(user_id: int) -> Dict[str, Any]:
        """Get user's work schedule preferences"""
        preferences = await UserPreferenceService.get_preferences(user_id)
        return preferences["productivity"]["work_hours"]