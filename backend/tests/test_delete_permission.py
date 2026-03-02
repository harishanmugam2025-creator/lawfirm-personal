import io
import os
from unittest.mock import AsyncMock, patch

os.environ["TESTING"] = "true"

import pytest
from fastapi.testclient import TestClient
from tests.conftest import TestingSessionLocal
from api.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_s3():
    with patch("services.document_service.s3_client") as mock_s3_client:
        yield mock_s3_client

@pytest.fixture(autouse=True)
def mock_opa():
    # Mock OPA to allow standard actions but we want to test the SERVICE logic
    # that checks ownership if can_delete_any is False.
    # We'll patch it to return False for "delete_any" for the second user.
    async def side_effect(role, resource, action):
        if resource == "documents" and action == "delete_any":
            return False
        return True
    
    with patch("services.opa_service.check_permission", side_effect=side_effect):
        yield

def _get_token(email, name):
    from models.otp import OTP
    from datetime import datetime, timedelta, timezone
    db = TestingSessionLocal()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.add(OTP(email=email, otp_code="123456", purpose="account_verification", expires_at=expires_at))
    db.commit()
    db.close()
    client.post("/api/auth/register", json={"name": name, "email": email, "password": "password123", "role": "associate"}, params={"otp_code": "123456"})
    resp = client.post("/api/auth/login", data={"username": email, "password": "password123"})
    return resp.json()["access_token"]

def test_delete_other_user_document_returns_403():
    token1 = _get_token("user1@example.com", "User One")
    token2 = _get_token("user2@example.com", "User Two")
    
    # User 1 uploads
    pdf_bytes = b"%PDF-1.0\n%%EOF"
    upload_resp = client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token1}"},
    )
    doc_id = upload_resp.json()["id"]
    
    # User 2 tries to delete
    delete_resp = client.delete(
        f"/api/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    
    assert delete_resp.status_code == 403
    assert "permission" in delete_resp.json()["detail"].lower()
