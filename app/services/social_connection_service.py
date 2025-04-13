from typing import Dict, List
import pandas as pd
from app.services.gmail_service import GmailService

class SocialConnectionService:
    def __init__(self, gmail_service: GmailService):
        self.gmail_service = gmail_service

    async def analyze_communication_patterns(self, timeframe: str = "week") -> Dict:
        email_data = await self.gmail_service.get_email_metadata(timeframe)

        df = pd.DataFrame(email_data)

        contacts_analysis = self._analyze_contacts(df)
        response_patterns = self._analyze_response_patterns(df)
        network_strength = self._calculate_network_strength(df)

        return {
            "contacts_analysis": contacts_analysis,
            "response_patterns": response_patterns,
            "network_strength": network_strength,
            "recommendations": self._generate_social_recommendations(
                contacts_analysis,
                response_patterns,
                network_strength
            )
        }

    def _analyze_contacts(self, df: pd.DataFrame) -> Dict:
        frequent_contacts = df.groupby('from_email').size().sort_values(ascending=False)
        return {
            "most_frequent": frequent_contacts.head(5).to_dict(),
            "total_unique_contacts": len(frequent_contacts)
        }

    def _analyze_response_patterns(self, df: pd.DataFrame) -> Dict:
        df['response_time'] = pd.to_datetime(df['response_timestamp']) - pd.to_datetime(df['timestamp'])
        return {
            "average_response_time": df['response_time'].mean().total_seconds() / 3600,
            "response_rate": len(df[df['responded']]) / len(df) * 100
        }

    def _calculate_network_strength(self, df: pd.DataFrame) -> Dict:
        return {
            "total_communications": len(df),
            "two_way_connections": len(df[df['responded']].groupby('from_email').filter(lambda x: len(x) > 1))
        }

    def _generate_social_recommendations(
        self,
        contacts_analysis: Dict,
        response_patterns: Dict,
        network_strength: Dict
    ) -> List[str]:
        recommendations = []

        if response_patterns["response_rate"] < 70:
            recommendations.append("Consider improving email response rate")

        if response_patterns["average_response_time"] > 24:
            recommendations.append("Try to reduce average response time")

        return recommendations