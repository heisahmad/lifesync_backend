import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from app.services.community_service import CommunityService
from app.models.user import User
from app.models.goal import Goal
from app.models.gamification import UserProfile, Badge
from app.utils.redis_utils import redis_cache

@pytest.fixture
def test_users():
    return [
        User(
            id=1,
            username="user1",
            email="user1@test.com",
            is_active=True
        ),
        User(
            id=2,
            username="user2",
            email="user2@test.com",
            is_active=True
        )
    ]

@pytest.fixture
def test_profiles(test_users):
    return [
        UserProfile(
            id=1,
            user_id=test_users[0].id,
            level=5,
            xp=1000,
            streak_count=7
        ),
        UserProfile(
            id=2,
            user_id=test_users[1].id,
            level=3,
            xp=500,
            streak_count=3
        )
    ]

@pytest.fixture
def test_goals(test_users):
    now = datetime.now()
    return [
        Goal(
            id=1,
            user_id=test_users[0].id,
            title="Daily 10K Steps",
            description="Walk 10,000 steps daily",
            category="health",
            target_value=10000,
            current_value=10000,
            is_public=True,
            completed=True,
            created_at=now - timedelta(days=7),
            completed_at=now,
            success_factors=["Regular walking breaks", "Morning jog"]
        ),
        Goal(
            id=2,
            user_id=test_users[1].id,
            title="Daily 10K Steps",
            description="Walk 10,000 steps daily",
            category="health",
            target_value=10000,
            current_value=8000,
            is_public=True,
            completed=False,
            created_at=now - timedelta(days=5)
        )
    ]

@pytest.fixture
def test_badges(test_profiles):
    return [
        Badge(
            id=1,
            name="Step Master",
            description="Completed step goal for 7 days",
            icon_url="/icons/steps.svg",
            user_profile_id=test_profiles[0].id
        ),
        Badge(
            id=2,
            name="Early Bird",
            description="Completed morning workout streak",
            icon_url="/icons/morning.svg",
            user_profile_id=test_profiles[0].id
        )
    ]

@pytest.fixture
def community_service(db_session):
    return CommunityService(db_session)

async def test_get_health_insights(community_service, test_users, mocker):
    # Mock health data
    mock_health_data = [
        {"timestamp": datetime.now(), "steps": 8000},
        {"timestamp": datetime.now(), "steps": 12000}
    ]
    
    mocker.patch.object(
        community_service,
        '_get_user_health_data',
        return_value=mock_health_data
    )
    
    insights = await community_service.get_health_insights("steps", "day")
    
    assert "average" in insights
    assert "median" in insights
    assert "trends" in insights
    assert insights["average"] == 10000

async def test_get_popular_goals(
    community_service,
    db_session,
    test_users,
    test_goals
):
    for goal in test_goals:
        db_session.add(goal)
    db_session.commit()
    
    goals = await community_service.get_popular_goals("health")
    
    assert len(goals) > 0
    assert "title" in goals[0]
    assert "completion_rate" in goals[0]
    assert "tips" in goals[0]

async def test_get_leaderboard(
    community_service,
    db_session,
    test_users,
    test_profiles,
    test_badges
):
    # Add test data to db
    for user in test_users:
        db_session.add(user)
    for profile in test_profiles:
        db_session.add(profile)
    for badge in test_badges:
        db_session.add(badge)
    db_session.commit()
    
    leaderboard = await community_service.get_leaderboard("health", "week")
    
    assert len(leaderboard) > 0
    assert "username" in leaderboard[0]
    assert "score" in leaderboard[0]
    assert "badges" in leaderboard[0]
    assert "streak" in leaderboard[0]

async def test_get_community_challenges(community_service):
    challenges = await community_service.get_community_challenges()
    
    assert len(challenges) > 0
    assert "id" in challenges[0]
    assert "title" in challenges[0]
    assert "participants" in challenges[0]
    assert "leaderboard" in challenges[0]

def test_analyze_trends(community_service):
    # Create test data
    data = {
        'timestamp': pd.date_range(start='2025-01-01', periods=30, freq='D'),
        'steps': np.random.randint(5000, 15000, 30)
    }
    df = pd.DataFrame(data)
    
    trends = community_service._analyze_trends(df, "steps")
    
    assert "direction" in trends
    assert "magnitude" in trends
    assert "weekly_avg" in trends

def test_analyze_time_patterns(community_service):
    # Create test data with timestamps
    data = {
        'timestamp': pd.date_range(
            start='2025-01-01',
            periods=24*7,
            freq='H'
        ),
        'steps': np.random.randint(100, 1000, 24*7)
    }
    df = pd.DataFrame(data)
    
    patterns = community_service._analyze_time_patterns(df, "steps")
    
    assert "peak_hours" in patterns
    assert "peak_days" in patterns
    assert "hourly_pattern" in patterns
    assert "daily_pattern" in patterns

async def test_calculate_user_score(
    community_service,
    db_session,
    test_users,
    test_profiles
):
    # Add test data
    db_session.add(test_users[0])
    db_session.add(test_profiles[0])
    db_session.commit()
    
    score = await community_service._calculate_user_score(
        test_users[0].id,
        "health",
        datetime.now() - timedelta(days=7)
    )
    
    assert score > 0

async def test_get_user_badges(
    community_service,
    db_session,
    test_users,
    test_profiles,
    test_badges
):
    # Add test data
    db_session.add(test_users[0])
    db_session.add(test_profiles[0])
    for badge in test_badges:
        db_session.add(badge)
    db_session.commit()
    
    badges = await community_service._get_user_badges(test_users[0].id)
    
    assert len(badges) > 0
    assert "name" in badges[0]
    assert "description" in badges[0]
    assert "icon" in badges[0]

async def test_get_goal_tips(community_service, test_goals):
    tips = await community_service._get_goal_tips(test_goals)
    
    assert len(tips) > 0
    assert isinstance(tips[0], str)

def test_calculate_average_duration(community_service, test_goals):
    duration = community_service._calculate_average_duration(test_goals)
    
    assert isinstance(duration, int)
    assert duration >= 0