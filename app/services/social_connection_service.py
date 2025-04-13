
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd

class SocialConnectionService:
    @staticmethod
    async def analyze_communication_patterns(email_data: List[Dict], calendar_data: List[Dict]) -> Dict:
        # Combine email and calendar interactions
        all_interactions = []
        
        for email in email_data:
            all_interactions.append({
                'contact': email['from'],
                'date': email['date'],
                'type': 'email'
            })
            
        for event in calendar_data:
            for attendee in event['attendees']:
                all_interactions.append({
                    'contact': attendee['email'],
                    'date': event['start_time'],
                    'type': 'meeting'
                })
                
        df = pd.DataFrame(all_interactions)
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate interaction frequencies
        contact_frequencies = df.groupby('contact').agg({
            'date': 'count'
        }).rename(columns={'date': 'interaction_count'})
        
        # Identify important contacts
        important_contacts = contact_frequencies[
            contact_frequencies['interaction_count'] > contact_frequencies['interaction_count'].mean()
        ].index.tolist()
        
        return {
            'important_contacts': important_contacts,
            'contact_frequencies': contact_frequencies.to_dict()
        }
        
    @staticmethod
    async def identify_important_dates(contacts: List[Dict]) -> List[Dict]:
        important_dates = []
        today = datetime.now()
        
        for contact in contacts:
            if 'birthday' in contact:
                birthday = datetime.strptime(contact['birthday'], '%Y-%m-%d')
                next_birthday = birthday.replace(year=today.year)
                
                if next_birthday < today:
                    next_birthday = next_birthday.replace(year=today.year + 1)
                    
                days_until = (next_birthday - today).days
                
                if days_until <= 30:
                    important_dates.append({
                        'contact': contact['name'],
                        'event': 'birthday',
                        'date': next_birthday.strftime('%Y-%m-%d'),
                        'days_until': days_until
                    })
                    
        return important_dates
        
    @staticmethod
    async def evaluate_connection_strength(interaction_history: List[Dict]) -> Dict:
        df = pd.DataFrame(interaction_history)
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate recency, frequency, and engagement scores
        now = datetime.now()
        df['days_ago'] = (now - df['date']).dt.days
        
        connection_scores = {}
        
        for contact in df['contact'].unique():
            contact_data = df[df['contact'] == contact]
            
            recency_score = 1 / (1 + contact_data['days_ago'].min())
            frequency_score = len(contact_data) / len(df)
            engagement_score = contact_data['duration'].mean() if 'duration' in contact_data else 0.5
            
            connection_scores[contact] = {
                'overall_score': (recency_score + frequency_score + engagement_score) / 3,
                'last_interaction': contact_data['date'].max().strftime('%Y-%m-%d'),
                'total_interactions': len(contact_data)
            }
            
        return connection_scores
