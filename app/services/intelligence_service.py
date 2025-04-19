from typing import Dict, List, Optional
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pandas as pd
from app.utils.redis_utils import redis_cache
from app.services.health_analysis_service import HealthAnalysisService
from app.services.financial_service import FinancialService
from app.services.social_connection_service import SocialConnectionService
from app.services.notification_service import NotificationService

class IntelligenceService:
    def __init__(self):
        self.health_service = HealthAnalysisService()
        self.financial_service = FinancialService()
        self.social_service = SocialConnectionService()
        self.notification_service = NotificationService()
        self.scaler = StandardScaler()
        
    async def analyze_behavior_patterns(self, user_id: int, timeframe: str = "week") -> Dict:
        # Get data from cache if available
        cache_key = f"behavior_patterns:{user_id}:{timeframe}"
        cached_patterns = await redis_cache.get_json(cache_key)
        if cached_patterns:
            return cached_patterns

        # Collect data from various services
        start_date = self._get_start_date(timeframe)
        
        health_data = await self.health_service.get_health_data(user_id, start_date)
        financial_data = await self.financial_service.get_finance_data(user_id, start_date)
        social_data = await self.social_service.get_social_data(user_id, start_date)
        
        # Combine and analyze data
        df = self._combine_data_sources(health_data, financial_data, social_data)
        
        patterns = {
            "work_patterns": await self._analyze_work_patterns(df),
            "health_patterns": await self._analyze_health_patterns(df),
            "social_patterns": await self._analyze_social_patterns(df),
            "anomalies": await self._detect_anomalies(df),
            "correlations": await self._analyze_correlations(df),
            "predictions": await self._generate_predictions(df)
        }
        
        # Cache results
        await redis_cache.set_json(cache_key, patterns, expiry=timedelta(hours=1))
        
        return patterns

    async def detect_burnout_risk(self, user_id: int) -> Dict:
        # Collect recent data
        recent_data = await self._get_recent_user_data(user_id)
        df = pd.DataFrame(recent_data)
        
        # Calculate risk factors
        risk_factors = {
            "work_hours": self._calculate_work_hours(df),
            "task_complexity": self._assess_task_complexity(df),
            "break_frequency": self._analyze_break_patterns(df),
            "sleep_quality": self._analyze_sleep_patterns(df),
            "stress_indicators": self._analyze_stress_indicators(df)
        }
        
        # Calculate overall risk score
        weights = {
            "work_hours": 0.3,
            "task_complexity": 0.15,
            "break_frequency": 0.2,
            "sleep_quality": 0.2,
            "stress_indicators": 0.15
        }
        
        risk_score = sum(score * weights[factor] for factor, score in risk_factors.items())
        
        # Generate recommendations
        recommendations = self._generate_burnout_recommendations(risk_factors, risk_score)
        
        # Notify user if risk is high
        if risk_score > 0.7:
            await self.notification_service.create_notification(
                user_id=user_id,
                notification_type="burnout_risk",
                message="High burnout risk detected. Consider taking a break.",
                priority="high"
            )
        
        return {
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "next_assessment": datetime.now() + timedelta(days=1)
        }

    async def analyze_mood(self, user_id: int) -> Dict:
        # Get recent data
        recent_data = await self._get_recent_user_data(user_id)
        df = pd.DataFrame(recent_data)
        
        # Analyze different mood indicators
        mood_indicators = {
            "activity_level": self._analyze_activity_level(df),
            "social_engagement": self._analyze_social_engagement(df),
            "sleep_quality": self._analyze_sleep_quality(df),
            "stress_level": self._analyze_stress_level(df),
            "productivity": self._analyze_productivity(df)
        }
        
        # Calculate overall mood score
        mood_score = sum(mood_indicators.values()) / len(mood_indicators)
        
        # Generate mood-based recommendations
        recommendations = self._generate_mood_recommendations(mood_indicators, mood_score)
        
        # Track mood trends
        await self._update_mood_trends(user_id, mood_score)
        
        return {
            "mood_score": mood_score,
            "indicators": mood_indicators,
            "recommendations": recommendations,
            "trends": await self._get_mood_trends(user_id)
        }

    async def process_voice_command(self, audio_file, user_id: int) -> Dict:
        from app.services.voice_service import VoiceService
        voice_service = VoiceService()
        return await voice_service.process_command(audio_file, user_id)

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

    def _combine_data_sources(self, health_data: Dict, financial_data: Dict, social_data: Dict) -> pd.DataFrame:
        """Combine and normalize data from different sources"""
        combined_data = []
        
        for date in set(health_data.keys()) | set(financial_data.keys()) | set(social_data.keys()):
            entry = {
                "date": date,
                **health_data.get(date, {}),
                **financial_data.get(date, {}),
                **social_data.get(date, {})
            }
            combined_data.append(entry)
            
        return pd.DataFrame(combined_data)

    async def _analyze_work_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze work patterns and productivity trends"""
        if df.empty:
            return {"error": "No data available"}
            
        patterns = {
            "peak_productivity_hours": self._find_peak_hours(df, "productivity"),
            "average_work_duration": float(df["work_duration"].mean()),
            "break_frequency": self._calculate_break_frequency(df),
            "task_completion_rate": self._calculate_task_completion_rate(df)
        }
        
        return patterns

    async def _analyze_health_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze health-related patterns"""
        if df.empty:
            return {"error": "No data available"}
            
        patterns = {
            "average_sleep_duration": float(df["sleep_duration"].mean()),
            "sleep_quality_trend": self._calculate_trend(df["sleep_quality"]),
            "exercise_consistency": self._calculate_consistency(df["exercise_minutes"]),
            "stress_level_trend": self._calculate_trend(df["stress_level"])
        }
        
        return patterns

    async def _analyze_correlations(self, df: pd.DataFrame) -> List[Dict]:
        """Find significant correlations between different metrics"""
        if df.empty:
            return []
            
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        corr_matrix = df[numeric_cols].corr()
        
        significant_correlations = []
        for i in range(len(numeric_cols)):
            for j in range(i+1, len(numeric_cols)):
                corr = corr_matrix.iloc[i, j]
                if abs(corr) >= 0.5:  # Only strong correlations
                    significant_correlations.append({
                        "factor1": numeric_cols[i],
                        "factor2": numeric_cols[j],
                        "correlation": float(corr)
                    })
                    
        return significant_correlations

    async def _detect_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Detect anomalies in user behavior"""
        if df.empty:
            return []
            
        numeric_data = df.select_dtypes(include=[np.number])
        scaled_data = self.scaler.fit_transform(numeric_data)
        
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomalies = iso_forest.fit_predict(scaled_data)
        
        anomaly_points = []
        for i, is_anomaly in enumerate(anomalies):
            if is_anomaly == -1:  # Anomaly detected
                anomaly_points.append({
                    "date": df.index[i].isoformat(),
                    "metrics": {
                        col: float(df.iloc[i][col])
                        for col in numeric_data.columns
                    }
                })
                
        return anomaly_points

    async def _generate_predictions(self, df: pd.DataFrame) -> Dict:
        """Generate predictions for various metrics"""
        if df.empty:
            return {}
            
        predictions = {}
        for col in df.select_dtypes(include=[np.number]).columns:
            if len(df[col]) >= 7:  # Need at least a week of data
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                X = np.arange(len(df[col])).reshape(-1, 1)
                y = df[col].values
                
                model.fit(X, y)
                
                # Predict next 7 days
                future_X = np.arange(len(df[col]), len(df[col])+7).reshape(-1, 1)
                predictions[col] = model.predict(future_X).tolist()
                
        return predictions

    def _calculate_trend(self, series: pd.Series) -> str:
        """Calculate trend direction and magnitude"""
        if len(series) < 2:
            return "insufficient_data"
            
        slope = np.polyfit(range(len(series)), series, 1)[0]
        
        if abs(slope) < 0.1:
            return "stable"
        return "increasing" if slope > 0 else "decreasing"

    def _calculate_consistency(self, series: pd.Series) -> float:
        """Calculate consistency score (0-1)"""
        if series.empty:
            return 0.0
            
        # Calculate coefficient of variation (lower is more consistent)
        cv = series.std() / series.mean() if series.mean() != 0 else float('inf')
        
        # Convert to 0-1 score (1 is most consistent)
        return float(1 / (1 + cv))

    def _find_peak_hours(self, df: pd.DataFrame, metric: str) -> List[int]:
        """Find hours with highest values for a given metric"""
        if metric not in df.columns:
            return []
            
        hourly_avg = df.groupby(df.index.hour)[metric].mean()
        return hourly_avg.nlargest(3).index.tolist()

    async def _update_mood_trends(self, user_id: int, mood_score: float):
        """Update mood trend data in cache"""
        trend_key = f"mood_trends:{user_id}"
        trends = await redis_cache.get_json(trend_key) or []
        
        trends.append({
            "timestamp": datetime.now().isoformat(),
            "score": mood_score
        })
        
        # Keep last 30 days
        trends = trends[-30:]
        await redis_cache.set_json(trend_key, trends)
