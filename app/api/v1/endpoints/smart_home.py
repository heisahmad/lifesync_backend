from fastapi import APIRouter, Depends, HTTPException, Body, WebSocket
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.smart_home import SmartDevice
from app.models.user import User
from app.services.notification_service import NotificationService
from typing import Dict, List
import httpx
import json
from datetime import datetime, time

router = APIRouter()
notification_service = NotificationService()

class AutomationRule:
    def __init__(self, trigger: Dict, action: Dict, conditions: List[Dict]):
        self.trigger = trigger
        self.action = action
        self.conditions = conditions

    async def evaluate(self, event: Dict, devices: List[SmartDevice]) -> bool:
        if not self._match_trigger(event):
            return False
            
        return all(self._check_condition(condition) for condition in self.conditions)
        
    def _match_trigger(self, event: Dict) -> bool:
        if self.trigger["type"] == "schedule":
            current_time = datetime.now().time()
            trigger_time = time.fromisoformat(self.trigger["value"])
            return current_time.hour == trigger_time.hour and current_time.minute == trigger_time.minute
        elif self.trigger["type"] == "device_state":
            return (
                event.get("device_id") == self.trigger["device_id"] and
                event.get("state", {}).get(self.trigger["property"]) == self.trigger["value"]
            )
        return False

    def _check_condition(self, condition: Dict) -> bool:
        if condition["type"] == "time_range":
            current_time = datetime.now().time()
            start_time = time.fromisoformat(condition["start"])
            end_time = time.fromisoformat(condition["end"])
            return start_time <= current_time <= end_time
        return True

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
        
        # Trigger automation rules
        await process_automation_rules(db, current_user.id, device, device.last_state)
        
        return response.json()

@router.post("/automation/rules")
async def create_automation_rule(
    rule_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate devices exist
    devices = db.query(SmartDevice).filter(
        SmartDevice.user_id == current_user.id
    ).all()
    device_ids = [d.id for d in devices]
    
    if (rule_data["trigger"].get("device_id") and 
        rule_data["trigger"]["device_id"] not in device_ids):
        raise HTTPException(status_code=400, detail="Trigger device not found")
        
    if rule_data["action"]["device_id"] not in device_ids:
        raise HTTPException(status_code=400, detail="Action device not found")
    
    # Store rule in Redis for quick access
    rule_key = f"automation_rule:{current_user.id}:{datetime.now().timestamp()}"
    await redis_cache.set_json(rule_key, rule_data)
    
    return {"rule_id": rule_key, "status": "created"}

@router.websocket("/devices/ws/{user_id}")
async def device_websocket(
    websocket: WebSocket,
    user_id: int,
    db: Session = Depends(get_db)
):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Process device state update
            device = db.query(SmartDevice).filter(
                SmartDevice.id == data["device_id"],
                SmartDevice.user_id == user_id
            ).first()
            
            if device:
                device.last_state = data["state"]
                db.commit()
                
                # Process automation rules
                await process_automation_rules(db, user_id, device, data["state"])
                
                # Send confirmation
                await websocket.send_json({"status": "processed"})
            else:
                await websocket.send_json({"error": "Device not found"})
    except Exception as e:
        await websocket.close()

async def process_automation_rules(
    db: Session,
    user_id: int,
    trigger_device: SmartDevice,
    device_state: Dict
):
    # Get all rules for user
    rule_pattern = f"automation_rule:{user_id}:*"
    rules = []
    
    async for key in redis_cache.redis_client.scan_iter(match=rule_pattern):
        rule_data = await redis_cache.get_json(key)
        if rule_data:
            rules.append(AutomationRule(
                rule_data["trigger"],
                rule_data["action"],
                rule_data.get("conditions", [])
            ))
    
    # Process each rule
    for rule in rules:
        event = {
            "device_id": trigger_device.id,
            "state": device_state,
            "timestamp": datetime.now().isoformat()
        }
        
        should_execute = await rule.evaluate(event, db.query(SmartDevice).filter(
            SmartDevice.user_id == user_id
        ).all())
        
        if should_execute:
            # Execute action
            action_device = db.query(SmartDevice).filter(
                SmartDevice.id == rule.action["device_id"],
                SmartDevice.user_id == user_id
            ).first()
            
            if action_device:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        action_device.webhook_url,
                        json=rule.action["command"],
                        headers={"X-Device-Secret": action_device.webhook_secret}
                    )
                
                # Notify user
                await notification_service.create_notification(
                    user_id=user_id,
                    notification_type="automation_triggered",
                    message=f"Automation rule triggered for {action_device.name}",
                    data={
                        "trigger_device": trigger_device.name,
                        "action_device": action_device.name,
                        "action": rule.action["command"]
                    }
                )
