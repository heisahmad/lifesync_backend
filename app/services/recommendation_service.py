from typing import Dict, List
import pandas as pd
from sklearn.ensemble import IsolationForest

class RecommendationService:
    @staticmethod
    async def generate_rule_based_recommendations(data: Dict) -> List[str]:
        recommendations = []

        # Health recommendations
        if data.get('health'):
            if data['health'].get('sleep_duration', 0) < 7:
                recommendations.append("Consider getting more sleep - aim for 7-9 hours")
            if data['health'].get('activity_level', 0) < 5000:
                recommendations.append("Try to increase your daily steps - aim for 10,000 steps")

        # Financial recommendations
        if data.get('finance'):
            if data['finance'].get('total_spending', 0) > 1000:
                recommendations.append("Consider reviewing your monthly budget")

        # Social recommendations
        if data.get('social'):
            if data['social'].get('missed_calls', 0) > 3:
                recommendations.append("You have several missed calls - consider following up")

        return recommendations

    @staticmethod
    async def detect_patterns(data: pd.DataFrame) -> Dict:
        # Use Isolation Forest for anomaly detection
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        predictions = iso_forest.fit_predict(data)

        return {
            "anomalies": (predictions == -1).sum(),
            "normal_patterns": (predictions == 1).sum()
        }
    
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