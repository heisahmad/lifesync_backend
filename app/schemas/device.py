from pydantic import BaseModel
from typing import Optional, Dict

class DeviceBase(BaseModel):
    device_type: str

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(DeviceBase):
    device_type: Optional[str] = None

class SyncQueueCreate(BaseModel):
    device_id: str
    data_type: str
    payload: Dict

class Device(DeviceBase):
    id: int
    device_id: str
    user_id: int

    class Config:
        from_attributes = True

class SyncQueue(BaseModel):
    id: int
    device_id: str
    data_type: str
    payload: Dict
    status: str = "pending"

    class Config:
        from_attributes = True