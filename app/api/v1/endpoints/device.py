
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.device import Device, SyncQueue
from app.schemas.device import DeviceCreate, DeviceUpdate, SyncQueueCreate
from typing import List
import uuid

router = APIRouter()

@router.post("/register")
async def register_device(
    device: DeviceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    device_id = str(uuid.uuid4())
    db_device = Device(
        user_id=current_user.id,
        device_id=device_id,
        device_type=device.device_type
    )
    db.add(db_device)
    db.commit()
    return {"device_id": device_id}

@router.post("/sync/queue")
async def queue_sync(
    queue_item: SyncQueueCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    device = db.query(Device).filter(
        Device.device_id == queue_item.device_id,
        Device.user_id == current_user.id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    sync_item = SyncQueue(
        device_id=queue_item.device_id,
        data_type=queue_item.data_type,
        payload=queue_item.payload
    )
    db.add(sync_item)
    db.commit()
    return {"status": "queued"}

@router.get("/sync/pending")
async def get_pending_syncs(
    device_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    device = db.query(Device).filter(
        Device.device_id == device_id,
        Device.user_id == current_user.id
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    pending_syncs = db.query(SyncQueue).filter(
        SyncQueue.device_id == device_id,
        SyncQueue.status == "pending"
    ).all()
    return pending_syncs
