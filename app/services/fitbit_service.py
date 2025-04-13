from fitbit import Fitbit
from datetime import datetime, timedelta

class FitbitService:
    def __init__(self, access_token, refresh_token):
        self.client = Fitbit(
            client_id=settings.FITBIT_CLIENT_ID,
            client_secret=settings.FITBIT_CLIENT_SECRET,
            access_token=access_token,
            refresh_token=refresh_token
        )
        
    async def get_activity_data(self, start_date=None, end_date=None):
        start_date = start_date or (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        
        return self.client.get_activity_summary(start_date, end_date)
        
    async def get_sleep_data(self, start_date=None, end_date=None):
        start_date = start_date or (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        
        return self.client.get_sleep(start_date, end_date)