import pytest
from datetime import datetime
from app.services.user_preference_service import UserPreferenceService
from app.utils.redis_utils import redis_cache

@pytest.fixture
def user_id():
    return 1

@pytest.fixture
async def preferences_service():
    # Clear any existing preferences before each test
    await redis_cache.delete_key("preferences:1")
    return UserPreferenceService()

async def test_get_default_preferences(preferences_service, user_id):
    preferences = await UserPreferenceService.get_preferences(user_id)
    assert preferences == UserPreferenceService.DEFAULT_PREFERENCES
    assert preferences["notifications"]["email"] is True
    assert preferences["privacy"]["share_health_data"] is False

async def test_update_preferences(preferences_service, user_id):
    new_preferences = {
        "notifications": {
            "email": False,
            "push": False
        }
    }
    
    updated = await UserPreferenceService.update_preferences(user_id, new_preferences)
    assert updated["notifications"]["email"] is False
    assert updated["notifications"]["push"] is False
    assert updated["notifications"]["web"] is True  # Unchanged value

async def test_update_category_preferences(preferences_service, user_id):
    new_health_prefs = {
        "daily_step_goal": 12000,
        "sleep_goal_hours": 9
    }
    
    updated = await UserPreferenceService.update_preferences(
        user_id,
        new_health_prefs,
        category="health"
    )
    assert updated["health"]["daily_step_goal"] == 12000
    assert updated["health"]["sleep_goal_hours"] == 9
    assert updated["health"]["workout_days"] == ["Mon", "Wed", "Fri"]  # Unchanged

async def test_reset_preferences(preferences_service, user_id):
    # First modify some preferences
    await UserPreferenceService.update_preferences(
        user_id,
        {"notifications": {"email": False}}
    )
    
    # Then reset
    reset = await UserPreferenceService.reset_preferences(user_id)
    assert reset["notifications"]["email"] is True  # Back to default

async def test_reset_category_preferences(preferences_service, user_id):
    # Modify health preferences
    await UserPreferenceService.update_preferences(
        user_id,
        {"daily_step_goal": 12000},
        category="health"
    )
    
    # Reset only health category
    reset = await UserPreferenceService.reset_preferences(user_id, category="health")
    assert reset["health"]["daily_step_goal"] == 10000  # Back to default
    
async def test_notification_settings(preferences_service, user_id):
    settings = await UserPreferenceService.get_notification_settings(user_id)
    assert "email" in settings
    assert "push" in settings
    assert "quiet_hours" in settings

async def test_should_send_notification_quiet_hours(preferences_service, user_id):
    # Enable quiet hours
    await UserPreferenceService.update_preferences(
        user_id,
        {
            "notifications": {
                "quiet_hours": {
                    "enabled": True,
                    "start": "22:00",
                    "end": "07:00"
                }
            }
        }
    )
    
    # Mock current time to be during quiet hours
    current_time = datetime.strptime("23:00", "%H:%M").time()
    should_send = await UserPreferenceService.should_send_notification(user_id, "email")
    assert should_send is False

async def test_integration_settings(preferences_service, user_id):
    # Test getting default settings
    fitbit_settings = await UserPreferenceService.get_integration_settings(user_id, "fitbit")
    assert fitbit_settings["sync_frequency"] == "hourly"
    
    # Test updating settings
    new_settings = {
        "sync_frequency": "30min",
        "metrics": ["steps", "heart_rate", "sleep", "activity"]
    }
    updated = await UserPreferenceService.update_integration_settings(
        user_id,
        "fitbit",
        new_settings
    )
    assert updated["sync_frequency"] == "30min"
    assert "activity" in updated["metrics"]

async def test_invalid_category(preferences_service, user_id):
    with pytest.raises(ValueError):
        await UserPreferenceService.update_preferences(
            user_id,
            {"invalid": "value"},
            category="invalid_category"
        )

async def test_invalid_integration(preferences_service, user_id):
    with pytest.raises(ValueError):
        await UserPreferenceService.get_integration_settings(
            user_id,
            "invalid_integration"
        )

async def test_health_goals(preferences_service, user_id):
    goals = await UserPreferenceService.get_health_goals(user_id)
    assert goals["daily_step_goal"] == 10000
    assert goals["sleep_goal_hours"] == 8
    assert "workout_days" in goals

async def test_work_schedule(preferences_service, user_id):
    schedule = await UserPreferenceService.get_work_schedule(user_id)
    assert schedule["start"] == "09:00"
    assert schedule["end"] == "17:00"