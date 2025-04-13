import pandas as pd
from sklearn.preprocessing import StandardScaler
from typing import Dict, List
from datetime import datetime, timedelta

class HealthAnalysisService:
    def __init__(self):
        self.scaler = StandardScaler()
        
    async def analyze_sleep_patterns(self, sleep_data: List[Dict]) -> Dict:
        df = pd.DataFrame(sleep_data)
        
        analysis = {
            "average_sleep_duration": df['duration'].mean() / 3600000,  # Convert ms to hours
            "sleep_efficiency": df['efficiency'].mean(),
            "deep_sleep_percentage": df['levels.summary.deep.percentage'].mean()
        }
        
        return analysis
        
    async def analyze_activity_patterns(self, activity_data: List[Dict]) -> Dict:
        df = pd.DataFrame(activity_data)
        
        analysis = {
            "average_steps": df['steps'].mean(),
            "average_calories": df['calories'].mean(),
            "active_minutes": df['veryActiveMinutes'].mean()
        }
        
        return analysis
        
    async def generate_health_recommendations(self, sleep_analysis: Dict, activity_analysis: Dict) -> List[str]:
        recommendations = []
        
        if sleep_analysis["average_sleep_duration"] < 7:
            recommendations.append("Consider getting more sleep - aim for 7-9 hours per night")
            
        if activity_analysis["average_steps"] < 10000:
            recommendations.append("Try to increase daily steps to reach 10,000 steps per day")
            
        return recommendations