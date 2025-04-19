from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.utils.redis_utils import redis_cache
from app.utils.logging_utils import logger
from app.models.user import User
from app.models.goal import Goal
from app.models.gamification import UserProfile
from app.services.user_service import UserService
from app.services.intelligence_service import IntelligenceService

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
        self.intelligence_service = IntelligenceService()

    async def get_system_metrics(self, timeframe: str = "24h") -> Dict[str, Any]:
        """Get system-wide performance and usage metrics"""
        start_time = self._get_start_time(timeframe)
        
        # Get metrics from Redis cache
        metrics = await self._collect_system_metrics(start_time)
        
        # Calculate derived metrics
        derived_metrics = await self._calculate_derived_metrics(metrics)
        
        # Get error statistics
        error_stats = await logger.get_error_stats(timeframe)
        
        # Combine all metrics
        return {
            "performance": {
                "api_latency": metrics["api_latency"],
                "error_rate": error_stats["total_errors"] / metrics["total_requests"] if metrics["total_requests"] > 0 else 0,
                "success_rate": metrics["successful_requests"] / metrics["total_requests"] if metrics["total_requests"] > 0 else 0
            },
            "usage": {
                "total_requests": metrics["total_requests"],
                "unique_users": metrics["unique_users"],
                "peak_times": metrics["peak_times"],
                "popular_endpoints": metrics["popular_endpoints"]
            },
            "errors": error_stats,
            "derived_metrics": derived_metrics
        }

    async def get_user_analytics(self, user_id: int, timeframe: str = "7d") -> Dict[str, Any]:
        """Get analytics for specific user"""
        start_time = self._get_start_time(timeframe)
        
        # Get user data
        user_data = await self._collect_user_data(user_id, start_time)
        
        # Get behavior patterns
        patterns = await self.intelligence_service.analyze_behavior_patterns(
            user_id,
            timeframe=timeframe
        )
        
        # Calculate engagement metrics
        engagement = await self._calculate_engagement_metrics(user_id, start_time)
        
        return {
            "activity": {
                "total_actions": user_data["total_actions"],
                "frequent_actions": user_data["frequent_actions"],
                "last_active": user_data["last_active"].isoformat()
            },
            "goals": {
                "total": user_data["total_goals"],
                "completed": user_data["completed_goals"],
                "completion_rate": user_data["goal_completion_rate"],
                "current_streak": user_data["current_streak"]
            },
            "engagement": engagement,
            "patterns": patterns
        }

    async def get_feature_usage(self, timeframe: str = "30d") -> Dict[str, Any]:
        """Analyze feature usage patterns"""
        start_time = self._get_start_time(timeframe)
        
        # Collect feature usage data
        usage_data = await self._collect_feature_usage(start_time)
        
        # Calculate feature engagement metrics
        engagement_metrics = self._calculate_feature_engagement(usage_data)
        
        # Get feature correlations
        correlations = await self._analyze_feature_correlations(usage_data)
        
        return {
            "popular_features": usage_data["popular_features"],
            "usage_trends": usage_data["usage_trends"],
            "engagement": engagement_metrics,
            "correlations": correlations,
            "recommendations": await self._generate_feature_recommendations(usage_data)
        }

    async def get_cohort_analysis(
        self,
        cohort_type: str = "registration_month",
        metric: str = "retention"
    ) -> Dict[str, Any]:
        """Analyze user cohorts based on specified criteria and metrics"""
        # Get user cohorts
        cohorts = await self._get_user_cohorts(cohort_type)
        
        # Calculate metrics for each cohort
        metrics = await self._calculate_cohort_metrics(cohorts, metric)
        
        # Analyze trends
        trends = self._analyze_cohort_trends(metrics)
        
        # Generate insights
        insights = await self._generate_cohort_insights(metrics)
        
        return {
            "cohorts": {
                cohort: {
                    "size": len(users),
                    "metrics": metrics[cohort]
                }
                for cohort, users in cohorts.items()
            },
            "trends": trends,
            "insights": insights
        }

    async def get_analytics_dashboard(self, timeframe: str = "30d") -> Dict[str, Any]:
        """Get a comprehensive analytics dashboard with key metrics"""
        # Get system metrics
        system_metrics = await self.get_system_metrics(timeframe)
        
        # Get feature usage analytics
        feature_usage = await self.get_feature_usage(timeframe)
        
        # Get cohort analysis
        cohort_analysis = await self.get_cohort_analysis()
        
        # Calculate key performance indicators
        kpis = await self._calculate_kpis(timeframe)
        
        return {
            "system_health": system_metrics,
            "feature_analytics": feature_usage,
            "user_cohorts": cohort_analysis,
            "kpis": kpis
        }

    async def _calculate_kpis(self, timeframe: str) -> Dict[str, Any]:
        """Calculate key performance indicators"""
        start_time = self._get_start_time(timeframe)
        
        # Get total users
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(
            User.last_login >= start_time
        ).count()
        
        # Get goal metrics
        goals = self.db.query(Goal).filter(
            Goal.created_at >= start_time
        ).all()
        completed_goals = len([g for g in goals if g.completed])
        
        # Calculate rates
        completion_rate = completed_goals / len(goals) if goals else 0
        retention_rate = active_users / total_users if total_users > 0 else 0
        
        return {
            "user_metrics": {
                "total_users": total_users,
                "active_users": active_users,
                "retention_rate": retention_rate
            },
            "goal_metrics": {
                "total_goals": len(goals),
                "completed_goals": completed_goals,
                "completion_rate": completion_rate
            }
        }

    def get_trending_features(self) -> List[Dict[str, Any]]:
        """Get list of trending features based on recent usage"""
        # Get feature usage data from Redis
        feature_data = redis_cache.lrange('feature_usage', 0, -1)
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(feature_data)
        if df.empty:
            return []
            
        # Calculate trends
        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        recent_usage = df[df['timestamp'] >= recent_cutoff]
        total_usage = df.groupby('feature_name').size()
        recent_usage = recent_usage.groupby('feature_name').size()
        
        # Calculate growth rate
        growth_rates = (recent_usage / total_usage * 100).fillna(0)
        
        # Get top trending features
        trending = growth_rates.nlargest(5)
        
        return [
            {
                "feature": feature,
                "growth_rate": rate,
                "total_uses": total_usage[feature]
            }
            for feature, rate in trending.items()
        ]

    async def _collect_system_metrics(self, start_time: datetime) -> Dict[str, Any]:
        """Collect system metrics from Redis cache"""
        metrics = {
            "api_latency": [],
            "total_requests": 0,
            "successful_requests": 0,
            "unique_users": set(),
            "peak_times": {},
            "popular_endpoints": {}
        }
        
        # Scan through Redis keys for metrics
        pattern = "metrics:*"
        async for key in redis_cache.redis_client.scan_iter(match=pattern):
            data = await redis_cache.get_json(key)
            if data and data["timestamp"] >= start_time.isoformat():
                metrics["api_latency"].append(data.get("latency", 0))
                metrics["total_requests"] += 1
                if data.get("status_code", 500) < 400:
                    metrics["successful_requests"] += 1
                
                metrics["unique_users"].add(data.get("user_id"))
                
                # Track peak times
                hour = datetime.fromisoformat(data["timestamp"]).strftime("%H:00")
                metrics["peak_times"][hour] = metrics["peak_times"].get(hour, 0) + 1
                
                # Track popular endpoints
                endpoint = data.get("endpoint", "unknown")
                metrics["popular_endpoints"][endpoint] = (
                    metrics["popular_endpoints"].get(endpoint, 0) + 1
                )
        
        # Convert unique users set to count
        metrics["unique_users"] = len(metrics["unique_users"])
        
        # Calculate average latency
        metrics["api_latency"] = (
            sum(metrics["api_latency"]) / len(metrics["api_latency"])
            if metrics["api_latency"]
            else 0
        )
        
        # Sort peak times and popular endpoints
        metrics["peak_times"] = dict(
            sorted(
                metrics["peak_times"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        )
        metrics["popular_endpoints"] = dict(
            sorted(
                metrics["popular_endpoints"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        )
        
        return metrics

    async def _calculate_derived_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived system metrics"""
        return {
            "requests_per_user": (
                metrics["total_requests"] / metrics["unique_users"]
                if metrics["unique_users"] > 0
                else 0
            ),
            "peak_load": max(metrics["peak_times"].values()) if metrics["peak_times"] else 0,
            "load_distribution": {
                hour: count / metrics["total_requests"] * 100
                for hour, count in metrics["peak_times"].items()
            } if metrics["total_requests"] > 0 else {},
            "endpoint_distribution": {
                endpoint: count / metrics["total_requests"] * 100
                for endpoint, count in metrics["popular_endpoints"].items()
            } if metrics["total_requests"] > 0 else {}
        }

    async def _collect_user_data(
        self,
        user_id: int,
        start_time: datetime
    ) -> Dict[str, Any]:
        """Collect user activity and goal data"""
        # Get user profile
        profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        # Get user goals
        goals = self.db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.created_at >= start_time
        ).all()
        
        # Get user actions from Redis
        actions = []
        pattern = f"user_action:{user_id}:*"
        async for key in redis_cache.redis_client.scan_iter(match=pattern):
            action = await redis_cache.get_json(key)
            if action and action["timestamp"] >= start_time.isoformat():
                actions.append(action)
        
        # Calculate metrics
        completed_goals = len([g for g in goals if g.completed])
        
        return {
            "total_actions": len(actions),
            "frequent_actions": self._get_frequent_actions(actions),
            "last_active": max([datetime.fromisoformat(a["timestamp"]) for a in actions]) if actions else datetime.now(),
            "total_goals": len(goals),
            "completed_goals": completed_goals,
            "goal_completion_rate": completed_goals / len(goals) if goals else 0,
            "current_streak": profile.streak_count if profile else 0
        }

    async def _calculate_engagement_metrics(
        self,
        user_id: int,
        start_time: datetime
    ) -> Dict[str, Any]:
        """Calculate user engagement metrics"""
        # Get daily active periods
        active_days = set()
        total_duration = timedelta()
        
        pattern = f"user_session:{user_id}:*"
        async for key in redis_cache.redis_client.scan_iter(match=pattern):
            session = await redis_cache.get_json(key)
            if session and session["start_time"] >= start_time.isoformat():
                session_start = datetime.fromisoformat(session["start_time"])
                session_end = datetime.fromisoformat(session["end_time"])
                
                active_days.add(session_start.date())
                total_duration += session_end - session_start
        
        total_days = (datetime.now() - start_time).days
        
        return {
            "daily_active_rate": len(active_days) / total_days if total_days > 0 else 0,
            "average_session_duration": (
                total_duration / len(active_days)
                if active_days
                else timedelta()
            ),
            "engagement_score": self._calculate_engagement_score(
                len(active_days),
                total_days,
                total_duration
            )
        }

    def _get_frequent_actions(self, actions: List[Dict]) -> Dict[str, int]:
        """Get most frequent user actions"""
        action_counts = {}
        for action in actions:
            action_type = action.get("type", "unknown")
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        return dict(
            sorted(
                action_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        )

    def _calculate_engagement_score(
        self,
        active_days: int,
        total_days: int,
        total_duration: timedelta
    ) -> float:
        """Calculate overall engagement score (0-100)"""
        if total_days == 0:
            return 0.0
            
        # Weights for different factors
        weights = {
            "activity_rate": 0.4,
            "duration": 0.3,
            "consistency": 0.3
        }
        
        # Activity rate score (0-1)
        activity_score = active_days / total_days
        
        # Duration score (0-1)
        avg_daily_hours = (total_duration.total_seconds() / 3600) / total_days
        duration_score = min(avg_daily_hours / 4, 1)  # Cap at 4 hours per day
        
        # Consistency score (0-1)
        consistency_score = 1 - (
            abs(active_days - total_days) / total_days
        )
        
        # Calculate weighted score
        total_score = (
            activity_score * weights["activity_rate"] +
            duration_score * weights["duration"] +
            consistency_score * weights["consistency"]
        )
        
        # Convert to 0-100 scale
        return round(total_score * 100, 2)

    def _get_start_time(self, timeframe: str) -> datetime:
        """Convert timeframe string to datetime"""
        now = datetime.now()
        
        if timeframe == "24h":
            return now - timedelta(hours=24)
        elif timeframe == "7d":
            return now - timedelta(days=7)
        elif timeframe == "30d":
            return now - timedelta(days=30)
        else:
            return now - timedelta(days=7)  # Default to 7 days

    async def _collect_feature_usage(self, start_time: datetime) -> Dict[str, Any]:
        """Collect feature usage data from Redis cache"""
        features = {}
        trends = {}
        
        # Scan through feature usage keys
        pattern = "feature_usage:*"
        async for key in redis_cache.redis_client.scan_iter(match=pattern):
            data = await redis_cache.get_json(key)
            if data and data["timestamp"] >= start_time.isoformat():
                feature = data.get("feature")
                if feature:
                    features[feature] = features.get(feature, 0) + 1
                    
                    # Track usage trends by day
                    day = datetime.fromisoformat(data["timestamp"]).strftime("%Y-%m-%d")
                    if day not in trends:
                        trends[day] = {}
                    trends[day][feature] = trends[day].get(feature, 0) + 1
        
        # Sort features by popularity
        popular_features = dict(
            sorted(
                features.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        )
        
        return {
            "popular_features": popular_features,
            "usage_trends": trends,
            "raw_data": features
        }

    def _calculate_feature_engagement(self, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate feature engagement metrics"""
        total_usage = sum(usage_data["raw_data"].values())
        
        # Calculate feature adoption rates
        adoption_rates = {
            feature: count / total_usage * 100
            for feature, count in usage_data["raw_data"].items()
        } if total_usage > 0 else {}
        
        # Calculate daily active features
        daily_features = {
            day: len(features)
            for day, features in usage_data["usage_trends"].items()
        }
        
        return {
            "adoption_rates": adoption_rates,
            "daily_active_features": daily_features,
            "total_feature_interactions": total_usage
        }

    async def _analyze_feature_correlations(self, usage_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze correlations between feature usage"""
        correlations = {}
        features = list(usage_data["raw_data"].keys())
        
        # Get user feature usage patterns
        user_patterns = {}
        pattern = "feature_usage:*"
        async for key in redis_cache.redis_client.scan_iter(match=pattern):
            data = await redis_cache.get_json(key)
            if data:
                user_id = data.get("user_id")
                feature = data.get("feature")
                if user_id and feature:
                    if user_id not in user_patterns:
                        user_patterns[user_id] = set()
                    user_patterns[user_id].add(feature)
        
        # Calculate feature correlations
        for i, feature1 in enumerate(features):
            for feature2 in features[i+1:]:
                both_count = sum(
                    1 for features in user_patterns.values()
                    if feature1 in features and feature2 in features
                )
                either_count = sum(
                    1 for features in user_patterns.values()
                    if feature1 in features or feature2 in features
                )
                
                correlation = both_count / either_count if either_count > 0 else 0
                correlations[f"{feature1}-{feature2}"] = correlation
        
        return dict(
            sorted(
                correlations.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        )

    async def _generate_feature_recommendations(self, usage_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate feature recommendations based on usage patterns"""
        recommendations = []
        
        # Get correlation data
        correlations = await self._analyze_feature_correlations(usage_data)
        
        # Generate recommendations based on popular features and correlations
        for feature_pair, correlation in correlations.items():
            feature1, feature2 = feature_pair.split("-")
            if correlation > 0.5:  # Strong correlation threshold
                recommendations.append({
                    "type": "feature_correlation",
                    "features": [feature1, feature2],
                    "correlation": correlation,
                    "message": f"Users who use {feature1} often also use {feature2}"
                })
        
        # Add recommendations for underutilized features
        avg_usage = sum(usage_data["raw_data"].values()) / len(usage_data["raw_data"])
        for feature, count in usage_data["raw_data"].items():
            if count < avg_usage * 0.5:  # Significantly underutilized
                recommendations.append({
                    "type": "underutilized_feature",
                    "feature": feature,
                    "usage_count": count,
                    "message": f"Feature {feature} is underutilized"
                })
        
        return recommendations[:5]  # Return top 5 recommendations

    async def _get_user_cohorts(self, cohort_type: str) -> Dict[str, List[int]]:
        """Get user cohorts based on specified criteria"""
        cohorts = {}
        
        if cohort_type == "registration_month":
            users = self.db.query(User).all()
            for user in users:
                cohort = user.created_at.strftime("%Y-%m")
                if cohort not in cohorts:
                    cohorts[cohort] = []
                cohorts[cohort].append(user.id)
                
        elif cohort_type == "activity_level":
            # Get user activity levels from Redis
            pattern = "user_activity:*"
            async for key in redis_cache.redis_client.scan_iter(match=pattern):
                data = await redis_cache.get_json(key)
                if data:
                    user_id = int(key.split(":")[-1])
                    activity_level = self._calculate_activity_level(data)
                    if activity_level not in cohorts:
                        cohorts[activity_level] = []
                    cohorts[activity_level].append(user_id)
        
        return cohorts

    async def _calculate_cohort_metrics(
        self,
        cohorts: Dict[str, List[int]],
        metric: str
    ) -> Dict[str, Dict[str, float]]:
        """Calculate metrics for each cohort"""
        metrics = {}
        
        for cohort_name, user_ids in cohorts.items():
            metrics[cohort_name] = {}
            
            if metric == "retention":
                metrics[cohort_name] = await self._calculate_retention_metrics(user_ids)
            elif metric == "engagement":
                metrics[cohort_name] = await self._calculate_cohort_engagement(user_ids)
            elif metric == "conversion":
                metrics[cohort_name] = await self._calculate_conversion_metrics(user_ids)
        
        return metrics

    def _analyze_cohort_trends(
        self,
        metrics: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """Analyze trends across cohorts"""
        trends = {
            "growth": [],
            "changes": [],
            "patterns": []
        }
        
        # Calculate growth between cohorts
        cohort_names = sorted(metrics.keys())
        for i in range(1, len(cohort_names)):
            prev_cohort = cohort_names[i-1]
            curr_cohort = cohort_names[i]
            
            for metric, value in metrics[curr_cohort].items():
                prev_value = metrics[prev_cohort].get(metric, 0)
                if prev_value > 0:
                    growth = (value - prev_value) / prev_value * 100
                    trends["growth"].append({
                        "metric": metric,
                        "cohorts": [prev_cohort, curr_cohort],
                        "growth": growth
                    })
        
        # Identify significant changes
        for growth in trends["growth"]:
            if abs(growth["growth"]) > 20:  # Significant change threshold
                trends["changes"].append({
                    "type": "significant_change",
                    "metric": growth["metric"],
                    "cohorts": growth["cohorts"],
                    "change": growth["growth"]
                })
        
        # Identify patterns
        if len(cohort_names) >= 3:
            for metric in metrics[cohort_names[0]].keys():
                values = [metrics[cohort][metric] for cohort in cohort_names]
                pattern = self._identify_trend_pattern(values)
                if pattern:
                    trends["patterns"].append({
                        "metric": metric,
                        "pattern": pattern
                    })
        
        return trends

    async def _generate_cohort_insights(
        self,
        metrics: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """Generate insights from cohort analysis"""
        insights = []
        trends = self._analyze_cohort_trends(metrics)
        
        # Add insights from significant changes
        for change in trends["changes"]:
            insights.append({
                "type": "cohort_change",
                "metric": change["metric"],
                "message": (
                    f"Significant {change['change']:.1f}% change in {change['metric']} "
                    f"between cohorts {change['cohorts'][0]} and {change['cohorts'][1]}"
                )
            })
        
        # Add insights from patterns
        for pattern in trends["patterns"]:
            insights.append({
                "type": "cohort_pattern",
                "metric": pattern["metric"],
                "message": f"Detected {pattern['pattern']} pattern in {pattern['metric']}"
            })
        
        return insights[:5]  # Return top 5 insights

    def _calculate_activity_level(self, activity_data: Dict[str, Any]) -> str:
        """Calculate user activity level based on activity data"""
        total_actions = activity_data.get("total_actions", 0)
        if total_actions >= 100:
            return "power_user"
        elif total_actions >= 50:
            return "active_user"
        elif total_actions >= 10:
            return "regular_user"
        else:
            return "casual_user"

    async def _calculate_retention_metrics(
        self,
        user_ids: List[int]
    ) -> Dict[str, float]:
        """Calculate retention metrics for a group of users"""
        metrics = {
            "day_1": 0,
            "day_7": 0,
            "day_30": 0
        }
        
        total_users = len(user_ids)
        if total_users == 0:
            return metrics
            
        for user_id in user_ids:
            # Get user's first activity
            first_activity = None
            pattern = f"user_action:{user_id}:*"
            async for key in redis_cache.redis_client.scan_iter(match=pattern):
                data = await redis_cache.get_json(key)
                if data:
                    timestamp = datetime.fromisoformat(data["timestamp"])
                    if not first_activity or timestamp < first_activity:
                        first_activity = timestamp
            
            if first_activity:
                # Check retention periods
                for action_key in redis_cache.redis_client.scan_iter(match=pattern):
                    data = await redis_cache.get_json(action_key)
                    if data:
                        timestamp = datetime.fromisoformat(data["timestamp"])
                        days_diff = (timestamp - first_activity).days
                        
                        if days_diff >= 1:
                            metrics["day_1"] += 1
                            break
                
                for action_key in redis_cache.redis_client.scan_iter(match=pattern):
                    data = await redis_cache.get_json(action_key)
                    if data:
                        timestamp = datetime.fromisoformat(data["timestamp"])
                        days_diff = (timestamp - first_activity).days
                        
                        if days_diff >= 7:
                            metrics["day_7"] += 1
                            break
                
                for action_key in redis_cache.redis_client.scan_iter(match=pattern):
                    data = await redis_cache.get_json(action_key)
                    if data:
                        timestamp = datetime.fromisoformat(data["timestamp"])
                        days_diff = (timestamp - first_activity).days
                        
                        if days_diff >= 30:
                            metrics["day_30"] += 1
                            break
        
        # Convert to percentages
        metrics = {
            period: count / total_users * 100
            for period, count in metrics.items()
        }
        
        return metrics

    async def _calculate_cohort_engagement(
        self,
        user_ids: List[int]
    ) -> Dict[str, float]:
        """Calculate engagement metrics for a group of users"""
        total_engagement = 0
        total_duration = timedelta()
        active_users = 0
        
        for user_id in user_ids:
            # Get user sessions
            pattern = f"user_session:{user_id}:*"
            user_active = False
            user_duration = timedelta()
            
            async for key in redis_cache.redis_client.scan_iter(match=pattern):
                session = await redis_cache.get_json(key)
                if session:
                    user_active = True
                    session_start = datetime.fromisoformat(session["start_time"])
                    session_end = datetime.fromisoformat(session["end_time"])
                    user_duration += session_end - session_start
            
            if user_active:
                active_users += 1
                total_duration += user_duration
                total_engagement += self._calculate_engagement_score(
                    active_days=1,  # Simplified for this calculation
                    total_days=1,
                    total_duration=user_duration
                )
        
        total_users = len(user_ids)
        return {
            "active_rate": active_users / total_users * 100 if total_users > 0 else 0,
            "avg_engagement": total_engagement / active_users if active_users > 0 else 0,
            "avg_session_duration": (
                total_duration / active_users if active_users > 0 else timedelta()
            ).total_seconds() / 3600  # Convert to hours
        }

    async def _calculate_conversion_metrics(
        self,
        user_ids: List[int]
    ) -> Dict[str, float]:
        """Calculate conversion metrics for a group of users"""
        total_users = len(user_ids)
        if total_users == 0:
            return {
                "goal_creation": 0,
                "goal_completion": 0,
                "premium_conversion": 0
            }
        
        metrics = {
            "created_goals": 0,
            "completed_goals": 0,
            "premium_users": 0
        }
        
        for user_id in user_ids:
            # Check goal metrics
            goals = self.db.query(Goal).filter(
                Goal.user_id == user_id
            ).all()
            
            if goals:
                metrics["created_goals"] += 1
                if any(goal.completed for goal in goals):
                    metrics["completed_goals"] += 1
            
            # Check premium status
            user = self.db.query(User).filter(User.id == user_id).first()
            if user and user.is_premium:
                metrics["premium_users"] += 1
        
        return {
            "goal_creation": metrics["created_goals"] / total_users * 100,
            "goal_completion": metrics["completed_goals"] / total_users * 100,
            "premium_conversion": metrics["premium_users"] / total_users * 100
        }

    def _identify_trend_pattern(self, values: List[float]) -> Optional[str]:
        """Identify pattern in a series of values"""
        if len(values) < 3:
            return None
            
        # Calculate differences between consecutive values
        diffs = [values[i+1] - values[i] for i in range(len(values)-1)]
        
        # Check for patterns
        is_increasing = all(d > 0 for d in diffs)
        is_decreasing = all(d < 0 for d in diffs)
        
        if is_increasing:
            return "increasing"
        elif is_decreasing:
            return "decreasing"
        
        # Check for cyclical pattern
        if len(values) >= 4:
            peaks = []
            troughs = []
            for i in range(1, len(values)-1):
                if values[i] > values[i-1] and values[i] > values[i+1]:
                    peaks.append(i)
                elif values[i] < values[i-1] and values[i] < values[i+1]:
                    troughs.append(i)
            
            if len(peaks) >= 2 and len(troughs) >= 2:
                return "cyclical"
        
        return "fluctuating"

    def track_feature_usage(self, user_id: int, feature_name: str, metadata: Dict[str, Any] = None) -> None:
        """
        Track when a user interacts with a specific feature
        """
        timestamp = datetime.utcnow()
        feature_data = {
            'user_id': user_id,
            'feature_name': feature_name,
            'timestamp': timestamp,
            'metadata': metadata or {}
        }
        redis_cache.rpush('feature_usage', feature_data)

    def get_feature_usage_stats(self, feature_name: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Get usage statistics for a specific feature within a date range
        """
        usage_data = redis_cache.lrange('feature_usage', 0, -1)
        df = pd.DataFrame(usage_data)
        
        mask = (
            (df['feature_name'] == feature_name) &
            (df['timestamp'] >= start_date) &
            (df['timestamp'] <= end_date)
        )
        filtered_df = df[mask]
        
        return {
            'total_uses': len(filtered_df),
            'unique_users': filtered_df['user_id'].nunique(),
            'usage_by_day': filtered_df.groupby(filtered_df['timestamp'].dt.date).size().to_dict(),
        }

    def analyze_user_cohorts(self, segment_by: str = 'registration_date') -> Dict[str, Any]:
        """
        Analyze user behavior patterns by different cohorts
        """
        def get_cohort_month(user: User) -> str:
            return user.created_at.strftime('%Y-%m')

        def get_engagement_metrics(users: List[User]) -> Dict[str, float]:
            total_goals = sum(len(user.goals) for user in users)
            return {
                'avg_goals_per_user': total_goals / len(users) if users else 0,
                'active_ratio': len([u for u in users if u.last_login > (datetime.utcnow() - timedelta(days=30))]) / len(users) if users else 0
            }

        users = self.db.query(User).all()
        cohorts = {}
        
        for user in users:
            cohort = get_cohort_month(user)
            if cohort not in cohorts:
                cohorts[cohort] = []
            cohorts[cohort].append(user)

        return {
            cohort: get_engagement_metrics(users)
            for cohort, users in cohorts.items()
        }

    @redis_cache.cache(expiration=3600)
    async def perform_cohort_analysis(self, timeframe: str = "monthly") -> Dict[str, Any]:
        """
        Perform cohort analysis to track user retention and engagement patterns.
        
        Args:
            timeframe: The time period for cohort analysis ("monthly" or "weekly")
            
        Returns:
            Dict containing cohort analysis results
        """
        users = await User.find_all().to_list()
        
        # Create DataFrame with user registration dates
        user_data = [{
            'user_id': user.id,
            'registration_date': user.created_at,
            'last_active': user.last_active
        } for user in users]
        
        df = pd.DataFrame(user_data)
        
        if timeframe == "monthly":
            df['cohort'] = df['registration_date'].dt.to_period('M')
            df['period'] = (df['last_active'].dt.to_period('M') - 
                          df['registration_date'].dt.to_period('M')).apply(lambda x: x.n)
        else:
            df['cohort'] = df['registration_date'].dt.to_period('W')
            df['period'] = (df['last_active'].dt.to_period('W') - 
                          df['registration_date'].dt.to_period('W')).apply(lambda x: x.n)
        
        # Create cohort matrix
        cohort_data = (df.groupby(['cohort', 'period'])
                      .size()
                      .unstack(fill_value=0))
        
        # Calculate retention rates
        retention_matrix = cohort_data.divide(cohort_data[0], axis=0) * 100
        
        return {
            'cohort_sizes': cohort_data[0].to_dict(),
            'retention_matrix': retention_matrix.to_dict(),
            'timeframe': timeframe
        }

    async def analyze_user_lifecycle(self) -> Dict[str, Any]:
        """
        Analyze user lifecycle stages and transitions.
        
        Returns:
            Dict containing user lifecycle analysis results
        """
        users = await User.find_all().to_list()
        goals = await Goal.find_all().to_list()
        
        # Define lifecycle stages
        stages = {
            'new': 0,
            'active': 0,
            'engaged': 0,
            'power_user': 0,
            'inactive': 0
        }
        
        now = datetime.utcnow()
        
        for user in users:
            days_since_last_active = (now - user.last_active).days
            completed_goals = len([g for g in goals if g.user_id == user.id and g.completed])
            
            if (now - user.created_at).days <= 7:
                stages['new'] += 1
            elif days_since_last_active > 30:
                stages['inactive'] += 1
            elif completed_goals >= 10 and days_since_last_active <= 3:
                stages['power_user'] += 1
            elif completed_goals >= 5:
                stages['engaged'] += 1
            else:
                stages['active'] += 1
        
        return {
            'lifecycle_stages': stages,
            'total_users': len(users),
            'timestamp': now.isoformat()
        }
