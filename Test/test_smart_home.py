import pytest
from fastapi.testclient import TestClient
from app.models.smart_home import SmartDevice
from app.api.v1.endpoints.smart_home import AutomationRule
from datetime import datetime, time

@pytest.fixture
def test_device():
    return SmartDevice(
        id=1,
        user_id=1,
        name="Test Light",
        device_type="light",
        webhook_url="http://test-device/webhook",
        webhook_secret="test-secret",
        config={
            "supports_dimming": True,
            "supports_color": True
        }
    )

@pytest.fixture
def test_automation_rule():
    return AutomationRule(
        trigger={
            "type": "schedule",
            "value": "08:00:00"
        },
        action={
            "device_id": 1,
            "command": {
                "power": "on",
                "brightness": 100
            }
        },
        conditions=[
            {
                "type": "time_range",
                "start": "06:00:00",
                "end": "22:00:00"
            }
        ]
    )

async def test_register_device(client: TestClient, test_user_token):
    response = client.post(
        "/api/v1/smart-home/devices",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "Test Light",
            "device_type": "light",
            "webhook_url": "http://test-device/webhook",
            "webhook_secret": "test-secret",
            "config": {
                "supports_dimming": True,
                "supports_color": True
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Light"
    assert data["device_type"] == "light"

async def test_send_device_command(
    client: TestClient,
    test_user_token,
    test_device,
    mocker
):
    # Mock the HTTP client response
    mock_response = mocker.patch("httpx.AsyncClient.post")
    mock_response.return_value.json.return_value = {
        "status": "success",
        "power": "on",
        "brightness": 100
    }

    response = client.post(
        f"/api/v1/smart-home/devices/{test_device.id}/command",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "power": "on",
            "brightness": 100
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["power"] == "on"

async def test_create_automation_rule(client: TestClient, test_user_token, test_device):
    response = client.post(
        "/api/v1/smart-home/automation/rules",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "trigger": {
                "type": "schedule",
                "value": "08:00:00"
            },
            "action": {
                "device_id": test_device.id,
                "command": {
                    "power": "on",
                    "brightness": 100
                }
            },
            "conditions": [
                {
                    "type": "time_range",
                    "start": "06:00:00",
                    "end": "22:00:00"
                }
            ]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "rule_id" in data
    assert data["status"] == "created"

def test_automation_rule_evaluation(test_automation_rule):
    # Test schedule trigger
    current_time = datetime.strptime("08:00:00", "%H:%M:%S").time()
    event = {"timestamp": datetime.now().isoformat()}
    
    # Override datetime.now() for testing
    monkeypatch.setattr(
        "datetime.datetime.now",
        lambda: datetime.combine(datetime.today(), current_time)
    )
    
    assert test_automation_rule._match_trigger(event)

    # Test condition evaluation
    assert test_automation_rule._check_condition({
        "type": "time_range",
        "start": "06:00:00",
        "end": "22:00:00"
    })

    # Test outside time range
    current_time = datetime.strptime("23:00:00", "%H:%M:%S").time()
    monkeypatch.setattr(
        "datetime.datetime.now",
        lambda: datetime.combine(datetime.today(), current_time)
    )
    
    assert not test_automation_rule._check_condition({
        "type": "time_range",
        "start": "06:00:00",
        "end": "22:00:00"
    })

async def test_device_websocket(
    client: TestClient,
    test_user_token,
    test_device
):
    with client.websocket_connect(
        f"/api/v1/smart-home/devices/ws/{test_device.user_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    ) as websocket:
        # Send device state update
        websocket.send_json({
            "device_id": test_device.id,
            "state": {
                "power": "on",
                "brightness": 75
            }
        })
        
        # Receive confirmation
        data = websocket.receive_json()
        assert data["status"] == "processed"

async def test_process_automation_rules(
    db_session,
    test_device,
    test_automation_rule,
    mocker
):
    # Mock Redis cache
    mock_redis = mocker.patch("app.utils.redis_utils.redis_cache")
    mock_redis.scan_iter.return_value = ["test_rule"]
    mock_redis.get_json.return_value = {
        "trigger": test_automation_rule.trigger,
        "action": test_automation_rule.action,
        "conditions": test_automation_rule.conditions
    }

    # Mock HTTP client
    mock_http = mocker.patch("httpx.AsyncClient.post")
    
    await process_automation_rules(
        db_session,
        test_device.user_id,
        test_device,
        {"power": "off"}
    )
    
    # Verify HTTP call was made with correct data
    mock_http.assert_called_once_with(
        test_device.webhook_url,
        json=test_automation_rule.action["command"],
        headers={"X-Device-Secret": test_device.webhook_secret}
    )