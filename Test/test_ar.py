import pytest
from fastapi.testclient import TestClient
from app.models.ar_data import ARLocation, ARObject
from app.api.v1.endpoints.ar import haversine_distance, validate_object_position
import math

@pytest.fixture
def test_location():
    return ARLocation(
        id=1,
        user_id=1,
        latitude=40.7128,
        longitude=-74.0060,
        altitude=10.0,
        name="Test Location",
        description="Test Description",
        tags=["test", "location"]
    )

@pytest.fixture
def test_object():
    return ARObject(
        id=1,
        location_id=1,
        name="Test Object",
        object_type="marker",
        position={"x": 0, "y": 0, "z": 0},
        scale={"x": 1, "y": 1, "z": 1},
        rotation={"x": 0, "y": 0, "z": 0}
    )

def test_haversine_distance():
    # Test known distances
    # New York to London approximately 5570 km
    ny_lat, ny_lon = 40.7128, -74.0060
    london_lat, london_lon = 51.5074, -0.1278
    
    distance = haversine_distance(ny_lat, ny_lon, london_lat, london_lon)
    assert abs(distance - 5570) < 100  # Allow some margin of error

    # Test same point
    distance = haversine_distance(ny_lat, ny_lon, ny_lat, ny_lon)
    assert distance == 0

async def test_create_location(client: TestClient, test_user_token):
    response = client.post(
        "/api/v1/ar/locations",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "latitude": 40.7128,
            "longitude": -74.0060,
            "altitude": 10.0,
            "name": "Test Location",
            "description": "Test Description",
            "tags": ["test", "location"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Location"
    assert data["latitude"] == 40.7128
    assert data["longitude"] == -74.0060

async def test_create_object(client: TestClient, test_user_token, test_location):
    response = client.post(
        f"/api/v1/ar/locations/{test_location.id}/objects",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "Test Object",
            "object_type": "marker",
            "position": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 1, "y": 1, "z": 1},
            "rotation": {"x": 0, "y": 0, "z": 0}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Object"
    assert data["object_type"] == "marker"

async def test_get_nearby_locations(client: TestClient, test_user_token, test_location):
    response = client.get(
        "/api/v1/ar/locations/nearby",
        headers={"Authorization": f"Bearer {test_user_token}"},
        params={
            "latitude": 40.7128,
            "longitude": -74.0060,
            "radius": 1.0
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == test_location.name

def test_validate_object_position():
    location = ARLocation(
        latitude=40.7128,
        longitude=-74.0060
    )

    # Test valid local position
    assert validate_object_position(location, {"x": 10, "y": 10, "z": 10})

    # Test invalid local position
    assert not validate_object_position(location, {"x": 200, "y": 200, "z": 200})

    # Test valid GPS position (within 100m)
    assert validate_object_position(location, {
        "latitude": 40.7129,
        "longitude": -74.0061
    })

    # Test invalid GPS position (too far)
    assert not validate_object_position(location, {
        "latitude": 40.7228,
        "longitude": -74.0160
    })

async def test_get_location_objects(
    client: TestClient,
    test_user_token,
    test_location,
    test_object
):
    response = client.get(
        f"/api/v1/ar/locations/{test_location.id}/objects",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == test_object.name