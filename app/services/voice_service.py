
import whisper
from fastapi import UploadFile
import tempfile
import os
from typing import Dict

class VoiceService:
    def __init__(self):
        self.model = whisper.load_model("base")
        self.commands = {
            "analyze": self._handle_analysis_command,
            "schedule": self._handle_schedule_command,
            "summary": self._handle_summary_command
        }

    async def process_command(self, audio_file: UploadFile, user_id: int) -> Dict:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Transcribe audio
            result = self.model.transcribe(temp_path)
            transcript = result["text"]

            # Process command
            command_type = self._identify_command_type(transcript)
            if command_type in self.commands:
                response = await self.commands[command_type](transcript, user_id)
            else:
                response = {"error": "Unknown command"}

            return {
                "transcript": transcript,
                "response": response
            }
        finally:
            os.unlink(temp_path)

    def _identify_command_type(self, transcript: str) -> str:
        transcript = transcript.lower()
        for command in self.commands.keys():
            if command in transcript:
                return command
        return "unknown"

    async def _handle_analysis_command(self, transcript: str, user_id: int) -> Dict:
        return {"message": "Analysis initiated", "status": "success"}

    async def _handle_schedule_command(self, transcript: str, user_id: int) -> Dict:
        return {"message": "Schedule updated", "status": "success"}

    async def _handle_summary_command(self, transcript: str, user_id: int) -> Dict:
        return {"message": "Summary generated", "status": "success"}