import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_clients():
    response = client.get("/api/v1/clients")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_client_profile():
    # First get a client
    clients_response = client.get("/api/v1/clients")
    if clients_response.json():
        client_id = clients_response.json()[0]["clientId"]
        
        profile_response = client.get(f"/api/v1/clients/{client_id}/profile")
        assert profile_response.status_code == 200
        assert "segment" in profile_response.json()

def test_create_action():
    action_data = {
        "clientId": "TEST_CLIENT",
        "actionType": "PROPOSE_PRODUCT",
        "product": "Test Product",
        "description": "Test action"
    }
    response = client.post("/api/v1/actions", json=action_data)
    assert response.status_code == 200
    assert "id" in response.json()
