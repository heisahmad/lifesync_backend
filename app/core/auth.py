from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings
from sqlalchemy.orm import Session
from app.models.integration import Integration
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from oauthlib.oauth2 import WebApplicationClient
import json
import requests

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.TOKEN_EXPIRY_HOURS * 60
SECRET_KEY = settings.SECRET_KEY

class OAuth2Manager:
    def __init__(self, db: Session):
        self.db = db

    async def refresh_token(self, integration: Integration) -> Dict:
        """Refresh OAuth2 token based on integration type"""
        if datetime.fromtimestamp(integration.expires_at) > datetime.now():
            return {
                "access_token": integration.access_token,
                "expires_at": integration.expires_at
            }

        try:
            if integration.type == "google":
                return await self._refresh_google_token(integration)
            elif integration.type == "fitbit":
                return await self._refresh_fitbit_token(integration)
            elif integration.type == "plaid":
                return await self._refresh_plaid_token(integration)
            else:
                raise ValueError(f"Unknown integration type: {integration.type}")
        except Exception as e:
            integration.is_active = False
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to refresh token: {str(e)}"
            )

    async def _refresh_google_token(self, integration: Integration) -> Dict:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        creds = Credentials.from_authorized_user_info(integration.credentials)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            integration.access_token = creds.token
            integration.expires_at = int(creds.expiry.timestamp())
            integration.credentials = creds.to_json()
            self.db.commit()
            return {
                "access_token": creds.token,
                "expires_at": int(creds.expiry.timestamp())
            }
        raise HTTPException(status_code=401, detail="Token expired and can't be refreshed")

    async def _refresh_fitbit_token(self, integration: Integration) -> Dict:
        import httpx
        
        token_url = "https://api.fitbit.com/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": integration.refresh_token,
            "client_id": settings.FITBIT_CLIENT_ID
        }
        headers = {"Authorization": f"Basic {settings.FITBIT_CLIENT_SECRET}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data, headers=headers)
            if response.status_code == 200:
                token_data = response.json()
                integration.access_token = token_data["access_token"]
                integration.refresh_token = token_data["refresh_token"]
                integration.expires_at = int(datetime.now().timestamp() + token_data["expires_in"])
                self.db.commit()
                return {
                    "access_token": token_data["access_token"],
                    "expires_at": integration.expires_at
                }
            raise HTTPException(status_code=401, detail="Failed to refresh Fitbit token")

    async def _refresh_plaid_token(self, integration: Integration) -> Dict:
        from plaid.api import plaid_api
        from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
        
        client = plaid_api.PlaidApi(settings.PLAID_CLIENT)
        request = ItemPublicTokenExchangeRequest(
            client_id=settings.PLAID_CLIENT_ID,
            secret=settings.PLAID_SECRET,
            public_token=integration.refresh_token
        )
        
        try:
            response = client.item_public_token_exchange(request)
            integration.access_token = response['access_token']
            integration.expires_at = int(datetime.now().timestamp() + 86400)  # 24 hours
            self.db.commit()
            return {
                "access_token": response['access_token'],
                "expires_at": integration.expires_at
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Failed to refresh Plaid token: {str(e)}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
