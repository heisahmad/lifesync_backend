import pytest
from fastapi.testclient import TestClient

def test_register(client):
    response = client.post("/api/v1/users/register", json={
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    })
    assert response.status_code == 200
    assert "id" in response.json()

def test_login(client):
    # First register
    client.post("/api/v1/users/register", json={
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    })
    
    # Then login
    response = client.post("/api/v1/users/token", data={
        "username": "test@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
