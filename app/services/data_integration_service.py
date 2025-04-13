
from typing import Dict, List
import pandas as pd
from datetime import datetime, timedelta

class DataIntegrationService:
    @staticmethod
    async def normalize_health_data(health_data: Dict) -> pd.DataFrame:
        df = pd.DataFrame(health_data)
        # Standardize date formats
        df['date'] = pd.to_datetime(df['date'])
        return df
        
    @staticmethod
    async def normalize_finance_data(finance_data: Dict) -> pd.DataFrame:
        df = pd.DataFrame(finance_data)
        df['date'] = pd.to_datetime(df['date'])
        df['amount'] = pd.to_numeric(df['amount'])
        return df
        
    @staticmethod
    async def combine_data_sources(health_df: pd.DataFrame, finance_df: pd.DataFrame) -> pd.DataFrame:
        # Merge data on date
        combined_df = pd.merge(health_df, finance_df, on='date', how='outer')
        combined_df = combined_df.sort_values('date')
        return combined_df
