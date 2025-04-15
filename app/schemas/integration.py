from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class IntegrationBase(BaseModel):
    type: str
    is_active: bool = True

class IntegrationCreate(IntegrationBase):
    access_token: str
    refresh_token: Optional[str] = None
    credentials: Optional[dict] = None
    expires_at: Optional[int] = None
    scopes: Optional[str] = None
    token_type: Optional[str] = None

class Integration(IntegrationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True