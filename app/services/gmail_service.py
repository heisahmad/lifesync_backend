
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from typing import List, Dict
import pandas as pd

class GmailService:
    def __init__(self, credentials_dict: Dict):
        credentials = Credentials.from_authorized_user_info(credentials_dict)
        self.service = build('gmail', 'v1', credentials=credentials)
        
    async def get_email_metadata(self, max_results: int = 100) -> List[Dict]:
        results = self.service.users().messages().list(
            userId='me',
            maxResults=max_results
        ).execute()
        
        messages = []
        for msg in results.get('messages', []):
            message = self.service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata'
            ).execute()
            messages.append(message)
            
        return messages
        
    async def analyze_communication_patterns(self, messages: List[Dict]) -> Dict:
        df = pd.DataFrame(messages)
        
        analysis = {
            "total_emails": len(messages),
            "emails_per_day": len(messages) / 30,  # Assuming 30-day period
            "top_senders": df.groupby('from').count().nlargest(5).to_dict(),
            "busiest_hours": df.groupby('timestamp').count().nlargest(5).to_dict()
        }
        
        return analysis
        
    async def identify_action_items(self, messages: List[Dict]) -> List[Dict]:
        action_items = []
        
        for message in messages:
            # Simple keyword-based action item detection
            keywords = ['todo', 'action item', 'please handle', 'deadline']
            if any(keyword in message.get('snippet', '').lower() for keyword in keywords):
                action_items.append({
                    "message_id": message['id'],
                    "snippet": message.get('snippet'),
                    "date": message.get('internalDate')
                })
                
        return action_items
