from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_user
from app.models.ar_data import ARLocation, ARObject
from app.models.user import User

router = APIRouter()

@router.post("/locations")
async def create_ar_location(
    location: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_location = ARLocation(
        user_id=current_user.id,
        **location
    )
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

@router.post("/locations/{location_id}/objects")
async def create_ar_object(
    location_id: int,
    object_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    location = db.query(ARLocation).filter(
        ARLocation.id == location_id,
        ARLocation.user_id == current_user.id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
        
    ar_object = ARObject(
        location_id=location_id,
        **object_data
    )
    db.add(ar_object)
    db.commit()
    db.refresh(ar_object)
    return ar_object

@router.get("/locations/nearby")
async def get_nearby_locations(
    latitude: float,
    longitude: float,
    radius: float = 1.0,  # km
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Basic proximity search
    locations = db.query(ARLocation).filter(
        ARLocation.latitude.between(latitude - radius/111, latitude + radius/111),
        ARLocation.longitude.between(longitude - radius/111, longitude + radius/111)
    ).all()
    return locations
