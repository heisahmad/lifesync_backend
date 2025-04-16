from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from typing import List, Dict
import pandas as pd
from datetime import datetime

class GmailService:
    def __init__(self, credentials_dict: Dict):
        credentials = Credentials.from_authorized_user_info(credentials_dict)
        self.service = build('gmail', 'v1', credentials=credentials)

    async def get_emails(self, max_results: int = 100, label_ids: List[str] = None) -> List[Dict]:
        query = {'userId': 'me', 'maxResults': max_results}
        if label_ids:
            query['labelIds'] = label_ids
        
        results = self.service.users().messages().list(**query).execute()
        messages = []
        
        for msg in results.get('messages', []):
            message = self.service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            messages.append(message)
            
        return messages

    async def create_label(self, name: str) -> Dict:
        label_object = {'name': name, 'messageListVisibility': 'show'}
        return self.service.users().labels().create(userId='me', body=label_object).execute()

    async def apply_label(self, message_id: str, label_ids: List[str]) -> Dict:
        return self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': label_ids}
        ).execute()

    async def send_email(self, to: str, subject: str, body: str) -> Dict:
        message = self._create_message(to, subject, body)
        return self.service.users().messages().send(userId='me', body=message).execute()

    def _create_message(self, to: str, subject: str, body: str) -> Dict:
        from email.mime.text import MIMEText
        import base64
        
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw}
