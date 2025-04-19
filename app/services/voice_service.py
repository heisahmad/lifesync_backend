import speech_recognition as sr
from typing import Dict, Any, Optional, BinaryIO
import json
import asyncio
from datetime import datetime
import tempfile
import os
import wave
from app.utils.redis_utils import redis_cache
from app.utils.logging_utils import logger
from app.services.intelligence_service import IntelligenceService
from app.services.notification_service import NotificationService
from app.services.smart_home import SmartHomeService
from app.services.schedule_optimizer import ScheduleOptimizer

class VoiceCommand:
    def __init__(self, command: str, params: Dict[str, Any]):
        self.command = command
        self.params = params
        self.timestamp = datetime.now()

class VoiceService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.intelligence_service = IntelligenceService()
        self.notification_service = NotificationService()
        self.smart_home_service = SmartHomeService()
        self.schedule_optimizer = ScheduleOptimizer()
        
        # Command patterns and their handlers
        self.command_patterns = {
            r"set.*reminder.*": self._handle_reminder_command,
            r"schedule.*meeting.*": self._handle_schedule_command,
            r"turn.*(?:on|off).*": self._handle_device_command,
            r"how.*doing.*": self._handle_status_query,
            r"analyze.*performance.*": self._handle_analysis_command,
            r"optimize.*schedule.*": self._handle_optimization_command
        }

    async def process_command(
        self,
        audio_file: BinaryIO,
        user_id: int
    ) -> Dict[str, Any]:
        """Process voice command from audio file"""
        try:
            # Convert audio to format recognizable by speech_recognition
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_path = temp_audio.name
                await self._normalize_audio(audio_file, temp_path)
                
                # Transcribe audio
                transcript = await self._transcribe_audio(temp_path)
                
                # Parse command
                command = await self._parse_command(transcript)
                
                if not command:
                    return {
                        "status": "error",
                        "message": "Could not parse command",
                        "transcript": transcript
                    }
                
                # Execute command
                result = await self._execute_command(command, user_id)
                
                # Cache command for analytics
                await self._cache_command(command, user_id, result)
                
                return {
                    "status": "success",
                    "command": command.command,
                    "result": result,
                    "transcript": transcript
                }
                
        except Exception as e:
            await logger.log_error(
                error=e,
                module="voice_service",
                function="process_command",
                user_id=user_id
            )
            return {
                "status": "error",
                "message": str(e)
            }

    async def _normalize_audio(self, audio_file: BinaryIO, output_path: str):
        """Normalize audio to format compatible with speech recognition"""
        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(16000)  # 16kHz
            wf.writeframes(audio_file.read())

    async def _transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio file to text"""
        with sr.AudioFile(audio_path) as source:
            try:
                audio = self.recognizer.record(source)
                return self.recognizer.recognize_google(audio)
            finally:
                # Clean up temporary file
                os.unlink(audio_path)

    async def _parse_command(self, transcript: str) -> Optional[VoiceCommand]:
        """Parse transcript into structured command"""
        import re
        
        transcript = transcript.lower()
        
        for pattern, handler in self.command_patterns.items():
            if re.search(pattern, transcript):
                command_type = pattern.split(r"[.\*]")[0]
                params = await self._extract_command_params(transcript, command_type)
                return VoiceCommand(command_type, params)
        
        return None

    async def _extract_command_params(
        self,
        transcript: str,
        command_type: str
    ) -> Dict[str, Any]:
        """Extract parameters from command transcript"""
        params = {}
        
        if command_type == "reminder":
            # Extract time and message
            import re
            time_match = re.search(r"(?:at|for)\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)", transcript)
            if time_match:
                params["time"] = time_match.group(1)
            
            message_match = re.search(r"to\s+(.+?)(?:\s+at|$)", transcript)
            if message_match:
                params["message"] = message_match.group(1)
                
        elif command_type == "schedule":
            # Extract meeting details
            import re
            title_match = re.search(r"schedule\s+(.+?)(?:\s+for|with|at|$)", transcript)
            if title_match:
                params["title"] = title_match.group(1)
            
            time_match = re.search(r"(?:at|for)\s+(\d{1,2}(?::\d{2})?(?:\s*[ap]m)?)", transcript)
            if time_match:
                params["time"] = time_match.group(1)
                
            participants_match = re.search(r"with\s+(.+?)(?:\s+at|$)", transcript)
            if participants_match:
                params["participants"] = [
                    p.strip() for p in participants_match.group(1).split(",")
                ]
                
        elif command_type == "turn":
            # Extract device and state
            import re
            device_match = re.search(r"turn\s+(?:on|off)\s+(?:the\s+)?(.+?)(?:\s+in|$)", transcript)
            if device_match:
                params["device"] = device_match.group(1)
            
            params["state"] = "on" if "turn on" in transcript else "off"
            
            location_match = re.search(r"in\s+(?:the\s+)?(.+?)(?:\s+at|$)", transcript)
            if location_match:
                params["location"] = location_match.group(1)
        
        return params

    async def _execute_command(
        self,
        command: VoiceCommand,
        user_id: int
    ) -> Dict[str, Any]:
        """Execute parsed command"""
        handler = self.command_patterns.get(
            f"^{command.command}.*",
            self._handle_unknown_command
        )
        return await handler(command.params, user_id)

    async def _handle_reminder_command(
        self,
        params: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Handle setting reminders"""
        if "time" not in params or "message" not in params:
            return {"error": "Missing time or message for reminder"}
            
        reminder_time = await self._parse_time(params["time"])
        
        await self.notification_service.schedule_notification(
            user_id=user_id,
            notification_type="reminder",
            message=params["message"],
            scheduled_time=reminder_time
        )
        
        return {
            "type": "reminder_set",
            "time": reminder_time.isoformat(),
            "message": params["message"]
        }

    async def _handle_schedule_command(
        self,
        params: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Handle scheduling meetings"""
        if "title" not in params or "time" not in params:
            return {"error": "Missing title or time for meeting"}
            
        meeting_time = await self._parse_time(params["time"])
        
        event = await self.schedule_optimizer.schedule_meeting(
            user_id=user_id,
            title=params["title"],
            start_time=meeting_time,
            duration=60,  # Default to 1 hour
            participants=params.get("participants", [])
        )
        
        return {
            "type": "meeting_scheduled",
            "event": event
        }

    async def _handle_device_command(
        self,
        params: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Handle smart device commands"""
        if "device" not in params or "state" not in params:
            return {"error": "Missing device or state information"}
            
        result = await self.smart_home_service.control_device(
            user_id=user_id,
            device_name=params["device"],
            command={
                "power": params["state"],
                "location": params.get("location")
            }
        )
        
        return {
            "type": "device_control",
            "device": params["device"],
            "state": params["state"],
            "result": result
        }

    async def _handle_status_query(
        self,
        params: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Handle status queries"""
        analysis = await self.intelligence_service.analyze_behavior_patterns(
            user_id,
            timeframe="day"
        )
        
        return {
            "type": "status_report",
            "patterns": analysis
        }

    async def _handle_analysis_command(
        self,
        params: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Handle performance analysis requests"""
        analysis = await self.intelligence_service.analyze_behavior_patterns(
            user_id,
            timeframe="week"
        )
        
        return {
            "type": "performance_analysis",
            "analysis": analysis
        }

    async def _handle_optimization_command(
        self,
        params: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Handle schedule optimization requests"""
        optimized = await self.schedule_optimizer.optimize_schedule(user_id)
        
        return {
            "type": "schedule_optimized",
            "changes": optimized
        }

    async def _handle_unknown_command(
        self,
        params: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Handle unknown commands"""
        return {
            "type": "unknown_command",
            "message": "Command not recognized"
        }

    async def _parse_time(self, time_str: str) -> datetime:
        """Parse time string into datetime object"""
        from datetime import datetime
        import re
        
        now = datetime.now()
        
        # Handle different time formats
        time_formats = [
            "%I:%M%p",  # 3:30pm
            "%I%p",     # 3pm
            "%H:%M",    # 15:30
            "%H"        # 15
        ]
        
        cleaned_time = time_str.lower().replace(" ", "")
        
        for fmt in time_formats:
            try:
                parsed_time = datetime.strptime(cleaned_time, fmt).time()
                return datetime.combine(now.date(), parsed_time)
            except ValueError:
                continue
                
        raise ValueError(f"Could not parse time: {time_str}")

    async def _cache_command(
        self,
        command: VoiceCommand,
        user_id: int,
        result: Dict[str, Any]
    ):
        """Cache command for analytics"""
        cache_key = f"voice_commands:{user_id}:{command.timestamp.timestamp()}"
        
        await redis_cache.set_json(
            cache_key,
            {
                "command": command.command,
                "params": command.params,
                "result": result,
                "timestamp": command.timestamp.isoformat()
            }
        )