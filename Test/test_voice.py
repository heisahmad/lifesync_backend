import pytest
from datetime import datetime
import io
import wave
import numpy as np
from app.services.voice_service import VoiceService, VoiceCommand
from unittest.mock import MagicMock, patch

@pytest.fixture
def voice_service():
    return VoiceService()

@pytest.fixture
def mock_audio_file():
    # Create a mock WAV file with 1 second of silence
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        # Generate 1 second of silence
        samples = np.zeros(16000, dtype=np.int16)
        wav.writeframes(samples.tobytes())
    
    buffer.seek(0)
    return buffer

@pytest.fixture
def test_user_id():
    return 1

async def test_process_command(voice_service, mock_audio_file, test_user_id, mocker):
    # Mock transcription
    mocker.patch.object(
        voice_service,
        '_transcribe_audio',
        return_value="set reminder to take a break at 3pm"
    )
    
    # Mock notification service
    mock_notification = mocker.patch.object(
        voice_service.notification_service,
        'schedule_notification'
    )
    
    result = await voice_service.process_command(mock_audio_file, test_user_id)
    
    assert result["status"] == "success"
    assert result["command"] == "reminder"
    assert "take a break" in result["result"]["message"]
    assert mock_notification.called

async def test_parse_reminder_command(voice_service):
    transcript = "set reminder to take a break at 3pm"
    command = await voice_service._parse_command(transcript)
    
    assert command is not None
    assert command.command == "set"
    assert "time" in command.params
    assert "message" in command.params
    assert command.params["time"] == "3pm"
    assert command.params["message"] == "take a break"

async def test_parse_schedule_command(voice_service):
    transcript = "schedule team meeting with John, Alice at 2:30pm"
    command = await voice_service._parse_command(transcript)
    
    assert command is not None
    assert command.command == "schedule"
    assert "title" in command.params
    assert "time" in command.params
    assert "participants" in command.params
    assert command.params["time"] == "2:30pm"
    assert len(command.params["participants"]) == 2

async def test_parse_device_command(voice_service):
    transcript = "turn on the living room lights"
    command = await voice_service._parse_command(transcript)
    
    assert command is not None
    assert command.command == "turn"
    assert "device" in command.params
    assert "state" in command.params
    assert command.params["device"] == "living room lights"
    assert command.params["state"] == "on"

async def test_handle_reminder_command(voice_service, test_user_id, mocker):
    params = {
        "time": "3:00pm",
        "message": "take a break"
    }
    
    # Mock notification service
    mock_notification = mocker.patch.object(
        voice_service.notification_service,
        'schedule_notification',
        return_value=None
    )
    
    result = await voice_service._handle_reminder_command(params, test_user_id)
    
    assert result["type"] == "reminder_set"
    assert "take a break" in result["message"]
    assert mock_notification.called

async def test_handle_schedule_command(voice_service, test_user_id, mocker):
    params = {
        "title": "team meeting",
        "time": "2:30pm",
        "participants": ["John", "Alice"]
    }
    
    # Mock schedule optimizer
    mock_schedule = mocker.patch.object(
        voice_service.schedule_optimizer,
        'schedule_meeting',
        return_value={"id": "123", "title": "team meeting"}
    )
    
    result = await voice_service._handle_schedule_command(params, test_user_id)
    
    assert result["type"] == "meeting_scheduled"
    assert "event" in result
    assert mock_schedule.called

async def test_handle_device_command(voice_service, test_user_id, mocker):
    params = {
        "device": "living room lights",
        "state": "on",
        "location": "living room"
    }
    
    # Mock smart home service
    mock_device = mocker.patch.object(
        voice_service.smart_home_service,
        'control_device',
        return_value={"status": "success"}
    )
    
    result = await voice_service._handle_device_command(params, test_user_id)
    
    assert result["type"] == "device_control"
    assert result["device"] == "living room lights"
    assert result["state"] == "on"
    assert mock_device.called

async def test_parse_time(voice_service):
    # Test various time formats
    test_cases = [
        ("3:30pm", "%I:%M%p"),
        ("3pm", "%I%p"),
        ("15:30", "%H:%M"),
        ("15", "%H")
    ]
    
    for time_str, _ in test_cases:
        result = await voice_service._parse_time(time_str)
        assert isinstance(result, datetime)

async def test_unknown_command(voice_service, test_user_id):
    params = {}
    result = await voice_service._handle_unknown_command(params, test_user_id)
    
    assert result["type"] == "unknown_command"
    assert "not recognized" in result["message"]

async def test_command_caching(voice_service, test_user_id, mocker):
    command = VoiceCommand("reminder", {
        "time": "3pm",
        "message": "take a break"
    })
    result = {
        "type": "reminder_set",
        "message": "take a break"
    }
    
    # Mock redis cache
    mock_cache = mocker.patch('app.utils.redis_utils.redis_cache.set_json')
    
    await voice_service._cache_command(command, test_user_id, result)
    
    assert mock_cache.called
    cache_data = mock_cache.call_args[0][1]
    assert cache_data["command"] == "reminder"
    assert "params" in cache_data
    assert "result" in cache_data