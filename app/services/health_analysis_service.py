
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict
from app.services.fitbit_service import FitbitService

class HealthAnalysisService:
    @staticmethod
    async def analyze_activity_patterns(date: str, fitbit_service: FitbitService) -> Dict:
        sleep_data = await fitbit_service.get_sleep_data(date)
        activity_data = await fitbit_service.get_activity_data(date)
        heart_rate_data = await fitbit_service.get_heart_rate(date)
        
        analysis = {
            "sleep_quality": analyze_sleep_quality(sleep_data),
            "activity_level": analyze_activity_level(activity_data),
            "stress_level": analyze_stress_level(heart_rate_data),
            "recommendations": generate_health_recommendations(sleep_data, activity_data, heart_rate_data)
        }
        
        return analysis
        
def analyze_sleep_quality(sleep_data: Dict) -> Dict:
    return {
        "total_sleep_hours": sleep_data.get("summary", {}).get("totalMinutesAsleep", 0) / 60,
        "deep_sleep_percentage": calculate_deep_sleep_percentage(sleep_data),
        "sleep_efficiency": sleep_data.get("summary", {}).get("efficiency", 0)
    }

def analyze_activity_level(activity_data: Dict) -> Dict:
    return {
        "steps": activity_data.get("summary", {}).get("steps", 0),
        "active_minutes": activity_data.get("summary", {}).get("veryActiveMinutes", 0),
        "calories_burned": activity_data.get("summary", {}).get("caloriesOut", 0)
    }

def analyze_stress_level(heart_rate_data: Dict) -> Dict:
    heart_rate_zones = heart_rate_data.get("activities-heart", [{}])[0].get("value", {}).get("heartRateZones", [])
    return {
        "resting_heart_rate": heart_rate_data.get("activities-heart", [{}])[0].get("value", {}).get("restingHeartRate", 0),
        "time_in_peak_zone": sum(zone.get("minutes", 0) for zone in heart_rate_zones if zone.get("name") == "Peak")
    }

def generate_health_recommendations(sleep_data: Dict, activity_data: Dict, heart_rate_data: Dict) -> list:
    recommendations = []
    
    sleep_hours = sleep_data.get("summary", {}).get("totalMinutesAsleep", 0) / 60
    if sleep_hours < 7:
        recommendations.append("Consider getting more sleep - aim for 7-9 hours")
        
    steps = activity_data.get("summary", {}).get("steps", 0)
    if steps < 10000:
        recommendations.append("Try to increase daily steps to reach 10,000 step goal")
        
    return recommendations
