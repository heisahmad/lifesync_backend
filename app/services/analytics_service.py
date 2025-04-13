
import pandas as pd
from typing import Dict, List
from sklearn.ensemble import IsolationForest

class AnalyticsService:
    @staticmethod
    async def analyze_time_series(data: pd.DataFrame, column: str) -> Dict:
        # Calculate basic time series metrics
        analysis = {
            'trend': data[column].diff().mean(),
            'volatility': data[column].std(),
            'peak_times': data.groupby(data['date'].dt.hour)[column].mean().nlargest(3).index.tolist()
        }
        return analysis
        
    @staticmethod
    async def detect_correlations(data: pd.DataFrame) -> Dict:
        # Calculate correlations between different metrics
        corr_matrix = data.corr()
        significant_correlations = {}
        
        for col1 in corr_matrix.columns:
            for col2 in corr_matrix.columns:
                if col1 < col2:  # Avoid duplicates
                    corr = corr_matrix.loc[col1, col2]
                    if abs(corr) > 0.5:  # Only strong correlations
                        significant_correlations[f"{col1}-{col2}"] = corr
                        
        return significant_correlations
        
    @staticmethod
    async def detect_anomalies(data: pd.DataFrame, column: str) -> List[Dict]:
        # Use Isolation Forest for anomaly detection
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomalies = iso_forest.fit_predict(data[[column]])
        
        anomaly_points = []
        for i, is_anomaly in enumerate(anomalies):
            if is_anomaly == -1:  # Anomaly detected
                anomaly_points.append({
                    'date': data.iloc[i]['date'],
                    'value': data.iloc[i][column]
                })
                
        return anomaly_points
