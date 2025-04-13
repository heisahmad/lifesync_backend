
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd

class GoogleCalendarService:
    def __init__(self, credentials_dict: Dict):
        credentials = Credentials.from_authorized_user_info(credentials_dict)
        self.service = build('calendar', 'v3', credentials=credentials)
        
    async def get_events(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        start = datetime.strptime(start_date, '%Y-%m-%d') if start_date else datetime.now()
        end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else (start + timedelta(days=30))
        
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=start.isoformat() + 'Z',
            timeMax=end.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
        
    async def analyze_calendar_density(self, events: List[Dict]) -> Dict:
        df = pd.DataFrame(events)
        
        analysis = {
            "total_events": len(events),
            "events_per_day": len(events) / 30,  # Assuming 30-day period
            "busy_hours": df.groupby('start.dateTime').count().max(),
            "common_meeting_times": df.groupby('start.dateTime').count().nlargest(3).to_dict()
        }
        
        return analysis
        
    async def find_free_blocks(self, events: List[Dict], min_duration: int = 30) -> List[Dict]:
        # Sort events by start time
        sorted_events = sorted(events, key=lambda x: x['start'].get('dateTime', x['start'].get('date')))
        free_blocks = []
        
        for i in range(len(sorted_events) - 1):
            current_end = datetime.fromisoformat(sorted_events[i]['end'].get('dateTime', sorted_events[i]['end'].get('date')))
            next_start = datetime.fromisoformat(sorted_events[i + 1]['start'].get('dateTime', sorted_events[i + 1]['start'].get('date')))
            
            duration = (next_start - current_end).total_seconds() / 60
            if duration >= min_duration:
                free_blocks.append({
                    "start": current_end.isoformat(),
                    "end": next_start.isoformat(),
                    "duration_minutes": duration
                })
                
        return free_blocks
