
import redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL)

def set_key(key: str, value: str, expiration: int = 3600):
    redis_client.setex(key, expiration, value)

def get_key(key: str) -> str:
    return redis_client.get(key)

def delete_key(key: str):
    redis_client.delete(key)
