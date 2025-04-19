from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict
from app.api.deps import get_db, get_current_user
from app.models.ar_data import ARLocation, ARObject
from app.models.user import User
from app.utils.redis_utils import redis_cache
from datetime import datetime, timedelta
import math

router = APIRouter()

EARTH_RADIUS = 6371  # kilometers

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on Earth"""
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return EARTH_RADIUS * c

@router.post("/locations")
async def create_ar_location(
    location: Dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate coordinates
    if not (-90 <= location["latitude"] <= 90 and -180 <= location["longitude"] <= 180):
        raise HTTPException(status_code=400, detail="Invalid coordinates")

    db_location = ARLocation(
        user_id=current_user.id,
        latitude=location["latitude"],
        longitude=location["longitude"],
        altitude=location.get("altitude", 0.0),
        name=location["name"],
        description=location.get("description", ""),
        meta_data=location.get("metadata", {}),
        tags=location.get("tags", [])
    )
    db.add(db_location)
    db.commit()
    db.refresh(db_location)

    # Cache location data for quick retrieval
    await redis_cache.set_json(
        f"ar_location:{db_location.id}",
        {
            "id": db_location.id,
            "latitude": db_location.latitude,
            "longitude": db_location.longitude,
            "name": db_location.name
        },
        expiry=timedelta(hours=24)
    )

    return db_location

@router.post("/locations/{location_id}/objects")
async def create_ar_object(
    location_id: int,
    object_data: Dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    location = db.query(ARLocation).filter(
        ARLocation.id == location_id,
        ARLocation.user_id == current_user.id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Validate object position relative to location
    if not validate_object_position(location, object_data["position"]):
        raise HTTPException(status_code=400, detail="Invalid object position")
        
    ar_object = ARObject(
        location_id=location_id,
        name=object_data["name"],
        object_type=object_data["object_type"],
        scale=object_data.get("scale", {"x": 1, "y": 1, "z": 1}),
        rotation=object_data.get("rotation", {"x": 0, "y": 0, "z": 0}),
        position=object_data["position"],
        meta_data=object_data.get("metadata", {}),
        tags=object_data.get("tags", [])
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
    max_results: int = 50,
    tags: Optional[List[str]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # First try to get from cache
    cache_key = f"nearby_locations:{latitude}:{longitude}:{radius}:{'-'.join(tags or [])}"
    cached_results = await redis_cache.get_json(cache_key)
    
    if cached_results:
        return cached_results

    # Calculate bounding box for initial filtering
    lat_range = radius / 111.0  # Roughly 111km per degree of latitude
    lon_range = radius / (111.0 * math.cos(math.radians(latitude)))
    
    # Query locations within bounding box
    query = db.query(ARLocation).filter(
        ARLocation.latitude.between(latitude - lat_range, latitude + lat_range),
        ARLocation.longitude.between(longitude - lon_range, longitude + lon_range)
    )
    
    # Apply tag filtering if specified
    if tags:
        query = query.filter(ARLocation.tags.overlap(tags))
    
    locations = query.all()
    
    # Calculate exact distances and filter
    nearby_locations = []
    for location in locations:
        distance = haversine_distance(
            latitude, longitude,
            location.latitude, location.longitude
        )
        if distance <= radius:
            location_data = {
                "id": location.id,
                "name": location.name,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "altitude": location.altitude,
                "description": location.description,
                "distance": round(distance, 3),
                "tags": location.tags
            }
            nearby_locations.append(location_data)
    
    # Sort by distance and limit results
    nearby_locations.sort(key=lambda x: x["distance"])
    nearby_locations = nearby_locations[:max_results]
    
    # Cache results
    await redis_cache.set_json(
        cache_key,
        nearby_locations,
        expiry=timedelta(minutes=5)
    )
    
    return nearby_locations

@router.get("/locations/{location_id}/objects")
async def get_location_objects(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    location = db.query(ARLocation).filter(
        ARLocation.id == location_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
        
    objects = db.query(ARObject).filter(
        ARObject.location_id == location_id
    ).all()
    
    return objects

def validate_object_position(location: ARLocation, position: Dict) -> bool:
    """Validate that an object's position is within reasonable bounds of its location"""
    # Convert position to lat/lon if needed
    if "latitude" in position and "longitude" in position:
        distance = haversine_distance(
            location.latitude, location.longitude,
            position["latitude"], position["longitude"]
        )
        # Object should be within 100 meters of location
        return distance <= 0.1
    
    # For local coordinate systems, validate bounds
    return (
        abs(position.get("x", 0)) <= 100 and
        abs(position.get("y", 0)) <= 100 and
        abs(position.get("z", 0)) <= 100
    )
