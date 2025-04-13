
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd

class ScheduleOptimizer:
    def __init__(self, calendar_service, health_service):
        self.calendar_service = calendar_service
        self.health_service = health_service
        
    async def optimize_schedule(self, start_date: str, end_date: str) -> Dict:
        # Get calendar events and health data
        events = await self.calendar_service.get_events(start_date, end_date)
        health_data = await self.health_service.get_health_data(start_date, end_date)
        
        # Find optimal meeting times based on energy levels
        optimal_times = await self.identify_optimal_times(events, health_data)
        
        # Find free blocks for task scheduling
        free_blocks = await self.calendar_service.find_free_blocks(events)
        
        # Generate schedule recommendations
        recommendations = await self.generate_recommendations(optimal_times, free_blocks, health_data)
        
        return {
            "optimal_meeting_times": optimal_times,
            "free_blocks": free_blocks,
            "recommendations": recommendations
        }
        
    async def identify_optimal_times(self, events: List[Dict], health_data: Dict) -> List[Dict]:
        # Analyze energy patterns from health data
        energy_patterns = pd.DataFrame(health_data.get('energy_levels', []))
        
        optimal_times = []
        for hour in range(9, 18):  # 9 AM to 6 PM
            avg_energy = energy_patterns[energy_patterns['hour'] == hour]['level'].mean()
            if avg_energy > 7:  # High energy threshold
                optimal_times.append({
                    "hour": hour,
                    "energy_level": avg_energy,
                    "recommendation": "Ideal for important meetings"
                })
                
        return optimal_times
        
    async def generate_recommendations(self, optimal_times: List[Dict], free_blocks: List[Dict], health_data: Dict) -> List[str]:
        recommendations = []
        
        # Generate time-based recommendations
        for time in optimal_times:
            recommendations.append(f"Schedule important meetings around {time['hour']}:00")
            
        # Generate health-based recommendations
        if health_data.get('sleep_quality', 0) < 0.7:
            recommendations.append("Consider scheduling lighter workload due to recent sleep patterns")
            
        return recommendations
