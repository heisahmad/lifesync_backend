import pytest
from datetime import datetime, timedelta
import json
from app.services.analytics_service import AnalyticsService
from app.models.user import User
from app.models.goal import Goal
from app.models.gamification import UserProfile
from app.utils.redis_utils import redis_cache

@pytest.fixture
def analytics_service(db_session):
    return AnalyticsService(db_session)

@pytest.fixture
def test_user_id():
    return 1

@pytest.fixture
def mock_redis_metrics():
    return [
        {
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "latency": 150,
            "status_code": 200,
            "user_id": 1,
            "endpoint": "/api/v1/goals"
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "latency": 200,
            "status_code": 400,
            "user_id": 2,
            "endpoint": "/api/v1/analytics"
        }
    ]

@pytest.fixture
def mock_user_actions():
    return [
        {
            "type": "goal_create",
            "timestamp": (datetime.now() - timedelta(hours=3)).isoformat()
        },
        {
            "type": "goal_complete",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
        },
        {
            "type": "goal_create",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat()
        }
    ]

@pytest.fixture
def mock_user_sessions():
    now = datetime.now()
    return [
        {
            "start_time": (now - timedelta(hours=4)).isoformat(),
            "end_time": (now - timedelta(hours=3)).isoformat()
        },
        {
            "start_time": (now - timedelta(hours=2)).isoformat(),
            "end_time": (now - timedelta(hours=1)).isoformat()
        }
    ]

async def test_get_system_metrics(
    analytics_service,
    mock_redis_metrics,
    mocker
):
    # Mock Redis cache
    mock_scan = mocker.patch('app.utils.redis_utils.redis_cache.redis_client.scan_iter')
    mock_scan.return_value = [f"metrics:{i}" for i in range(len(mock_redis_metrics))]
    
    mock_get = mocker.patch('app.utils.redis_utils.redis_cache.get_json')
    mock_get.side_effect = mock_redis_metrics
    
    # Mock error stats
    mock_error_stats = mocker.patch(
        'app.utils.logging_utils.logger.get_error_stats',
        return_value={"total_errors": 1}
    )
    
    metrics = await analytics_service.get_system_metrics("24h")
    
    assert "performance" in metrics
    assert "usage" in metrics
    assert "errors" in metrics
    assert "derived_metrics" in metrics
    assert metrics["usage"]["total_requests"] == len(mock_redis_metrics)
    assert metrics["usage"]["unique_users"] == 2

async def test_get_user_analytics(
    analytics_service,
    test_user_id,
    mock_user_actions,
    mock_user_sessions,
    db_session,
    mocker
):
    # Create test user and profile
    user = User(id=test_user_id, username="testuser")
    profile = UserProfile(
        user_id=test_user_id,
        streak_count=5,
        level=3,
        xp=1000
    )
    db_session.add(user)
    db_session.add(profile)
    
    # Create test goals
    goals = [
        Goal(
            user_id=test_user_id,
            title="Test Goal 1",
            completed=True,
            created_at=datetime.now() - timedelta(days=3)
        ),
        Goal(
            user_id=test_user_id,
            title="Test Goal 2",
            completed=False,
            created_at=datetime.now() - timedelta(days=2)
        )
    ]
    for goal in goals:
        db_session.add(goal)
    db_session.commit()
    
    # Mock Redis cache for user actions
    mock_action_scan = mocker.patch(
        'app.utils.redis_utils.redis_cache.redis_client.scan_iter'
    )
    mock_action_scan.return_value = [
        f"user_action:{test_user_id}:{i}"
        for i in range(len(mock_user_actions))
    ]
    
    mock_action_get = mocker.patch(
        'app.utils.redis_utils.redis_cache.get_json'
    )
    mock_action_get.side_effect = mock_user_actions + mock_user_sessions
    
    # Mock behavior patterns
    mock_patterns = mocker.patch(
        'app.services.intelligence_service.IntelligenceService.analyze_behavior_patterns',
        return_value={"pattern": "test"}
    )
    
    analytics = await analytics_service.get_user_analytics(test_user_id, "7d")
    
    assert "activity" in analytics
    assert "goals" in analytics
    assert "engagement" in analytics
    assert "patterns" in analytics
    assert analytics["goals"]["total"] == 2
    assert analytics["goals"]["completed"] == 1
    assert analytics["goals"]["completion_rate"] == 0.5
    assert analytics["goals"]["current_streak"] == 5

def test_get_frequent_actions(analytics_service, mock_user_actions):
    frequent_actions = analytics_service._get_frequent_actions(mock_user_actions)
    
    assert len(frequent_actions) <= 5
    assert "goal_create" in frequent_actions
    assert frequent_actions["goal_create"] == 2

def test_calculate_engagement_score(analytics_service):
    score = analytics_service._calculate_engagement_score(
        active_days=5,
        total_days=7,
        total_duration=timedelta(hours=10)
    )
    
    assert isinstance(score, float)
    assert 0 <= score <= 100

def test_get_start_time(analytics_service):
    now = datetime.now()
    
    # Test different timeframes
    assert analytics_service._get_start_time("24h") > now - timedelta(days=1)
    assert analytics_service._get_start_time("7d") > now - timedelta(days=7)
    assert analytics_service._get_start_time("30d") > now - timedelta(days=30)
    
    # Test default
    assert analytics_service._get_start_time("invalid") > now - timedelta(days=7)

async def test_collect_system_metrics(
    analytics_service,
    mock_redis_metrics,
    mocker
):
    # Mock Redis cache
    mock_scan = mocker.patch(
        'app.utils.redis_utils.redis_cache.redis_client.scan_iter'
    )
    mock_scan.return_value = [f"metrics:{i}" for i in range(len(mock_redis_metrics))]
    
    mock_get = mocker.patch('app.utils.redis_utils.redis_cache.get_json')
    mock_get.side_effect = mock_redis_metrics
    
    metrics = await analytics_service._collect_system_metrics(
        datetime.now() - timedelta(hours=24)
    )
    
    assert "api_latency" in metrics
    assert "total_requests" in metrics
    assert "unique_users" in metrics
    assert "peak_times" in metrics
    assert "popular_endpoints" in metrics
    assert metrics["total_requests"] == len(mock_redis_metrics)

async def test_calculate_engagement_metrics(
    analytics_service,
    test_user_id,
    mock_user_sessions,
    mocker
):
    # Mock Redis cache for sessions
    mock_scan = mocker.patch(
        'app.utils.redis_utils.redis_cache.redis_client.scan_iter'
    )
    mock_scan.return_value = [
        f"user_session:{test_user_id}:{i}"
        for i in range(len(mock_user_sessions))
    ]
    
    mock_get = mocker.patch('app.utils.redis_utils.redis_cache.get_json')
    mock_get.side_effect = mock_user_sessions
    
    engagement = await analytics_service._calculate_engagement_metrics(
        test_user_id,
        datetime.now() - timedelta(days=1)
    )
    
    assert "daily_active_rate" in engagement
    assert "average_session_duration" in engagement
    assert "engagement_score" in engagement
    assert isinstance(engagement["daily_active_rate"], float)
    assert 0 <= engagement["daily_active_rate"] <= 1