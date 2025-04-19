from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.utils.redis_utils import redis_cache
from app.utils.logging_utils import logger
from app.models.user import User
from app.models.goal import Goal
from app.models.gamification import UserProfile, Badge
from app.services.user_preference_service import UserPreferenceService

class CommunityService:
    def __init__(self, db: Session):
        self.db = db
        self.preference_service = UserPreferenceService()

    async def get_health_insights(self, metric: str, timeframe: str = "week") -> Dict:
        """Get community health insights for specific metric"""
        # Get users who share health data
        users = await self._get_users_sharing_data("health")
        if not users:
            return {"error": "No shared data available"}

        start_date = self._get_start_date(timeframe)
        
        # Collect and analyze data
        all_data = []
        for user in users:
            data = await self._get_user_health_data(user.id, metric, start_date)
            if data:
                all_data.extend(data)

        if not all_data:
            return {"error": "No data available for the specified metric"}

        df = pd.DataFrame(all_data)
        
        analysis = {
            "average": float(df[metric].mean()),
            "median": float(df[metric].median()),
            "percentiles": {
                "25": float(df[metric].quantile(0.25)),
                "75": float(df[metric].quantile(0.75)),
                "90": float(df[metric].quantile(0.90))
            },
            "trends": self._analyze_trends(df, metric),
            "time_patterns": self._analyze_time_patterns(df, metric)
        }

        # Cache results
        cache_key = f"community_health:{metric}:{timeframe}"
        await redis_cache.set_json(cache_key, analysis, expiry=timedelta(hours=1))

        return analysis

    async def get_popular_goals(self, category: str) -> List[Dict]:
        """Get popular community goals with success rates"""
        goals = self.db.query(Goal).filter(
            Goal.category == category,
            Goal.is_public == True
        ).all()

        goal_stats = []
        for goal in goals:
            similar_goals = self.db.query(Goal).filter(
                Goal.title.ilike(f"%{goal.title}%"),
                Goal.category == category
            ).all()

            total = len(similar_goals)
            completed = len([g for g in similar_goals if g.completed])
            
            if total >= 5:  # Only include goals attempted by multiple users
                goal_stats.append({
                    "title": goal.title,
                    "category": goal.category,
                    "total_attempts": total,
                    "completion_rate": round(completed / total * 100, 2),
                    "average_duration": self._calculate_average_duration(similar_goals),
                    "tips": await self._get_goal_tips(similar_goals)
                })

        return sorted(goal_stats, key=lambda x: x["completion_rate"], reverse=True)

    async def analyze_trends(self, category: str, timeframe: str = "month") -> Dict:
        """Analyze community trends for specific category"""
        users = await self._get_users_sharing_data(category)
        if not users:
            return {"error": "No shared data available"}

        start_date = self._get_start_date(timeframe)
        
        # Collect data based on category
        if category == "health":
            data = await self._collect_health_trends(users, start_date)
        elif category == "productivity":
            data = await self._collect_productivity_trends(users, start_date)
        elif category == "social":
            data = await self._collect_social_trends(users, start_date)
        else:
            return {"error": "Invalid category"}

        # Analyze trends
        df = pd.DataFrame(data)
        
        analysis = {
            "overall_trend": self._calculate_trend_direction(df),
            "peak_times": self._find_peak_times(df),
            "correlations": await self._find_correlations(df),
            "anomalies": await self._detect_anomalies(df),
            "recommendations": await self._generate_trend_recommendations(df, category)
        }

        return analysis

    async def get_leaderboard(
        self,
        category: str,
        timeframe: str = "week",
        limit: int = 10
    ) -> List[Dict]:
        """Get community leaderboard for specific category"""
        users = await self._get_users_sharing_data(category)
        if not users:
            return []

        start_date = self._get_start_date(timeframe)
        
        leaderboard = []
        for user in users:
            score = await self._calculate_user_score(user.id, category, start_date)
            if score > 0:
                leaderboard.append({
                    "user_id": user.id,
                    "username": user.username,
                    "score": score,
                    "badges": await self._get_user_badges(user.id),
                    "streak": await self._get_user_streak(user.id)
                })

        return sorted(leaderboard, key=lambda x: x["score"], reverse=True)[:limit]

    async def get_community_challenges(self) -> List[Dict]:
        """Get active community challenges"""
        cache_key = "community_challenges"
        challenges = await redis_cache.get_json(cache_key)
        
        if not challenges:
            challenges = [
                {
                    "id": "step_challenge",
                    "title": "10K Steps Daily",
                    "description": "Maintain 10,000 steps daily for a week",
                    "category": "health",
                    "duration": "7d",
                    "participants": await self._get_challenge_participants("step_challenge"),
                    "leaderboard": await self._get_challenge_leaderboard("step_challenge")
                },
                {
                    "id": "meditation_challenge",
                    "title": "Daily Meditation",
                    "description": "Meditate for 10 minutes daily",
                    "category": "wellness",
                    "duration": "30d",
                    "participants": await self._get_challenge_participants("meditation_challenge"),
                    "leaderboard": await self._get_challenge_leaderboard("meditation_challenge")
                }
            ]
            
            await redis_cache.set_json(cache_key, challenges, expiry=timedelta(hours=1))
        
        return challenges

    def _get_start_date(self, timeframe: str) -> datetime:
        now = datetime.now()
        if timeframe == "day":
            return now - timedelta(days=1)
        elif timeframe == "week":
            return now - timedelta(days=7)
        elif timeframe == "month":
            return now - timedelta(days=30)
        else:
            return now - timedelta(days=7)

    async def _get_users_sharing_data(self, category: str) -> List[User]:
        """Get users who have opted to share their data"""
        return self.db.query(User).join(UserProfile).filter(
            User.is_active == True
        ).all()

    def _analyze_trends(self, df: pd.DataFrame, metric: str) -> Dict:
        """Analyze trends in time series data"""
        if df.empty:
            return {}

        # Calculate rolling averages
        df['rolling_avg'] = df[metric].rolling(window=7).mean()
        
        # Calculate trend
        slope = np.polyfit(range(len(df)), df[metric].fillna(0), 1)[0]
        
        return {
            "direction": "increasing" if slope > 0 else "decreasing",
            "magnitude": abs(slope),
            "weekly_avg": float(df['rolling_avg'].mean())
        }

    def _analyze_time_patterns(self, df: pd.DataFrame, metric: str) -> Dict:
        """Analyze patterns by time of day/week"""
        if df.empty:
            return {}

        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        df['day'] = pd.to_datetime(df['timestamp']).dt.day_name()
        
        hourly_avg = df.groupby('hour')[metric].mean()
        daily_avg = df.groupby('day')[metric].mean()
        
        return {
            "peak_hours": hourly_avg.nlargest(3).index.tolist(),
            "peak_days": daily_avg.nlargest(3).index.tolist(),
            "hourly_pattern": hourly_avg.to_dict(),
            "daily_pattern": daily_avg.to_dict()
        }

    async def _get_goal_tips(self, goals: List[Goal]) -> List[str]:
        """Extract tips from successful goals"""
        tips = []
        for goal in goals:
            if goal.completed and goal.success_factors:
                tips.extend(goal.success_factors)
        
        # Return unique tips, prioritizing most common ones
        from collections import Counter
        tip_counts = Counter(tips)
        return [tip for tip, _ in tip_counts.most_common(5)]

    def _calculate_average_duration(self, goals: List[Goal]) -> int:
        """Calculate average days to complete goals"""
        durations = []
        for goal in goals:
            if goal.completed and goal.completed_at:
                duration = (goal.completed_at - goal.created_at).days
                if duration > 0:
                    durations.append(duration)
        
        return int(np.mean(durations)) if durations else 0

    async def _calculate_user_score(
        self,
        user_id: int,
        category: str,
        start_date: datetime
    ) -> float:
        """Calculate user score for leaderboard"""
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if not profile:
            return 0.0
            
        base_score = profile.xp * 0.5  # 50% from XP
        streak_bonus = profile.streak_count * 10  # 10 points per day streak
        
        # Category-specific scoring
        if category == "health":
            health_score = await self._calculate_health_score(user_id, start_date)
            return base_score + streak_bonus + health_score
        elif category == "productivity":
            productivity_score = await self._calculate_productivity_score(user_id, start_date)
            return base_score + streak_bonus + productivity_score
        
        return base_score + streak_bonus

    async def _get_user_badges(self, user_id: int) -> List[Dict]:
        """Get user's badges for leaderboard"""
        badges = self.db.query(Badge).join(UserProfile).filter(
            UserProfile.user_id == user_id
        ).all()
        
        return [{
            "name": badge.name,
            "description": badge.description,
            "icon": badge.icon_url
        } for badge in badges]

    async def _get_user_streak(self, user_id: int) -> int:
        """Get user's current streak"""
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        return profile.streak_count if profile else 0
