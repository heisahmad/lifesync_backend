
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.smart_home import SmartDevice
from app.models.user import User
import httpx
import json

router = APIRouter()

@router.post("/devices")
async def register_device(
    device_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    device = SmartDevice(
        user_id=current_user.id,
        name=device_data["name"],
        device_type=device_data["device_type"],
        webhook_url=device_data["webhook_url"],
        webhook_secret=device_data.get("webhook_secret"),
        config=device_data.get("config", {})
    )
    db.add(device)
    db.commit()
    return device

@router.post("/devices/{device_id}/command")
async def send_device_command(
    device_id: int,
    command: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    device = db.query(SmartDevice).filter(
        SmartDevice.id == device_id,
        SmartDevice.user_id == current_user.id
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    async with httpx.AsyncClient() as client:
        response = await client.post(
            device.webhook_url,
            json=command,
            headers={"X-Device-Secret": device.webhook_secret}
        )
        device.last_state = response.json()
        db.commit()
        return response.json()
