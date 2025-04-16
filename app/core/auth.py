from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from oauthlib.oauth2 import WebApplicationClient
import json
import requests

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key-keep-it-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

GOOGLE_CLIENT_ID = "your-google-client-id"
GOOGLE_CLIENT_SECRET = "your-google-client-secret"
APPLE_CLIENT_ID = "your-apple-client-id"
APPLE_CLIENT_SECRET = "your-apple-client-secret"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_google_token(token: str) -> Dict:
    try:
        google_client = WebApplicationClient(GOOGLE_CLIENT_ID)
        userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
        uri = google_client.prepare_request_uri(userinfo_endpoint, token=token)
        response = requests.get(uri)
        if response.status_code != 200:
            return None
        return response.json()
    except Exception:
        return None

async def verify_apple_token(token: str) -> Dict:
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            'https://appleid.apple.com/auth/oauth2/v1/userinfo', 
            headers=headers
        )
        if response.status_code != 200:
            return None
        return response.json()
    except Exception:
        return None
