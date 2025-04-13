
from typing import List, Dict
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

class RecommendationService:
    def __init__(self):
        self.model = RandomForestClassifier()
        
    async def generate_rule_based_recommendations(self, user_data: Dict) -> List[str]:
        recommendations = []
        
        # Sleep recommendations
        if user_data.get('sleep_hours', 0) < 7:
            recommendations.append("Consider going to bed earlier to improve sleep quality")
            
        # Exercise recommendations
        if user_data.get('daily_steps', 0) < 8000:
            recommendations.append("Try to increase your daily step count")
            
        # Financial recommendations
        if user_data.get('monthly_savings_rate', 0) < 0.2:
            recommendations.append("Consider setting up automatic savings transfers")
            
        return recommendations
        
    async def generate_ml_recommendations(self, historical_data: pd.DataFrame) -> List[str]:
        # Train model on historical patterns
        features = ['sleep_quality', 'activity_level', 'stress_level']
        target = 'productivity_score'
        
        self.model.fit(historical_data[features], historical_data[target])
        
        # Generate predictions and recommendations
        predictions = self.model.predict(historical_data[features].tail(1))
        
        recommendations = []
        if predictions[0] < historical_data[target].mean():
            recommendations.append("Your predicted productivity might be lower than usual")
            
        return recommendations
        
    async def personalize_recommendations(self, recommendations: List[str], user_preferences: Dict) -> List[str]:
        # Filter and prioritize based on user preferences
        priority_areas = user_preferences.get('priority_areas', [])
        
        prioritized_recommendations = []
        other_recommendations = []
        
        for rec in recommendations:
            is_priority = any(area.lower() in rec.lower() for area in priority_areas)
            if is_priority:
                prioritized_recommendations.append(rec)
            else:
                other_recommendations.append(rec)
                
        return prioritized_recommendations + other_recommendations
