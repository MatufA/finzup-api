import pytest
from fastapi.testclient import TestClient
from finzup_api.main import app
from finzup_api.auth import create_access_token
import json
import os

client = TestClient(app)

@pytest.fixture
def test_user():
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }

@pytest.fixture
def test_token(test_user):
    return create_access_token("test_user_id")

def test_register(test_user):
    response = client.post("/api/v1/auth/register", json=test_user)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login(test_user):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_process_invoice(test_token):
    # Create a test image file
    test_image_path = "test_invoice.jpg"
    with open(test_image_path, "wb") as f:
        f.write(b"fake image content")
    
    try:
        with open(test_image_path, "rb") as f:
            response = client.post(
                "/api/v1/process-invoice",
                files={"file": ("test_invoice.jpg", f, "image/jpeg")},
                headers={"Authorization": f"Bearer {test_token}"}
            )
        
        assert response.status_code in [200, 400]  # Either success or error depending on image content
        if response.status_code == 200:
            data = response.json()
            assert "invoiceNumber" in data
            assert "invoiceDate" in data
            assert "supplier" in data
            assert "recipient" in data
            assert "items" in data
            assert "totalAmountNis" in data
    finally:
        if os.path.exists(test_image_path):
            os.remove(test_image_path)

def test_get_audit_logs(test_token):
    response = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_invalid_file_type(test_token):
    # Create a test file with invalid extension
    test_file_path = "test.txt"
    with open(test_file_path, "w") as f:
        f.write("test content")
    
    try:
        with open(test_file_path, "rb") as f:
            response = client.post(
                "/api/v1/process-invoice",
                files={"file": ("test.txt", f, "text/plain")},
                headers={"Authorization": f"Bearer {test_token}"}
            )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    finally:
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def test_unauthorized_access():
    response = client.get("/api/v1/audit-logs")
    assert response.status_code == 401 