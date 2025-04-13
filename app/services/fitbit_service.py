
from typing import Dict, Optional
import httpx
from app.core.config import settings

class FitbitService:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.fitbit.com/1/user/-"
        
    async def get_sleep_data(self, date: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/sleep/date/{date}.json",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            return response.json()
            
    async def get_activity_data(self, date: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/activities/date/{date}.json",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            return response.json()
            
    async def get_heart_rate(self, date: str) -> Dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/activities/heart/date/{date}/1d.json",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            return response.json()
