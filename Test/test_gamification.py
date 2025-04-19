import pytest
from datetime import datetime, timedelta
from app.services.gamefication_service import GamificationService
from app.models.gamification import UserProfile, Badge, UserBadge
from app.models.goal import Goal

@pytest.fixture
def gamification_service():
    return GamificationService()

@pytest.fixture
def test_user_profile():
    return UserProfile(
        id=1,
        user_id=1,
        level=1,
        xp=0,
        streak_count=0,
        last_activity=datetime.now()
    )

@pytest.fixture
def test_goal():
    return Goal(
        id=1,
        user_id=1,
        title="Test Goal",
        description="Test Description",
        category="health",
        target_value=100,
        current_value=100,
        completed=True
    )

async def test_process_progress(db_session, gamification_service, test_user_profile, test_goal):
    db_session.add(test_user_profile)
    db_session.add(test_goal)
    db_session.commit()

    result = await gamification_service.process_progress(db_session, 1, test_goal)
    
    assert "profile" in result
    assert "rewards" in result
    assert result["profile"]["level"] >= 1
    assert result["profile"]["xp"] > 0
    assert any(reward["type"] == "xp" for reward in result["rewards"])

async def test_streak_maintenance(db_session, gamification_service, test_user_profile):
    test_user_profile.last_activity = datetime.now() - timedelta(hours=23)
    test_user_profile.streak_count = 1
    db_session.add(test_user_profile)
    db_session.commit()

    result = await gamification_service.process_progress(
        db_session, 
        test_user_profile.user_id, 
        test_goal
    )
    
    assert result["profile"]["streak"] == 2
    assert any(reward["type"] == "streak" for reward in result["rewards"])

async def test_level_up(db_session, gamification_service, test_user_profile, test_goal):
    test_user_profile.xp = 990
    db_session.add(test_user_profile)
    db_session.commit()

    result = await gamification_service.process_progress(db_session, 1, test_goal)
    
    assert result["profile"]["level"] == 2
    assert any(reward["type"] == "level_up" for reward in result["rewards"])

async def test_achievement_unlock(db_session, gamification_service, test_user_profile, test_goal):
    test_user_profile.streak_count = 6
    db_session.add(test_user_profile)
    db_session.commit()

    result = await gamification_service.process_progress(db_session, 1, test_goal)
    
    assert any(
        reward["type"] == "achievement" and 
        reward["name"] == "consistency_king" 
        for reward in result["rewards"]
    )

async def test_multiplier_calculation(gamification_service, test_user_profile):
    # Test base multiplier
    multiplier = gamification_service._calculate_multiplier(test_user_profile)
    assert multiplier == 1.0

    # Test level bonus
    test_user_profile.level = 5
    multiplier = gamification_service._calculate_multiplier(test_user_profile)
    assert multiplier > 1.0

    # Test streak bonus
    test_user_profile.streak_count = 5
    multiplier = gamification_service._calculate_multiplier(test_user_profile)
    assert multiplier > 1.5