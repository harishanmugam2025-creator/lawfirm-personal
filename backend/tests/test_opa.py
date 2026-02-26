"""Tests for OPA integration.

These tests mock the OPA HTTP server so they can run without a live OPA
instance. They verify:
  - ``opa_service.check_permission`` allow / deny logic
  - ``opa_service.get_allowed_actions`` returns structured data
  - ``require_permission`` dependency raises 403 on deny
  - ``GET /auth/permissions`` returns the user's allowed actions
  - Fail-closed behaviour when OPA is unreachable
"""

import io
import uuid
import os
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["TESTING"] = "true"

import services.opa_service # Ensure it is imported before patching
from api.main import app
from models.database import Base, get_db

# ── Test database setup ──

TEST_DATABASE_URL = "sqlite:///./test_veritas.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"


def _register_and_login(role: str = "associate") -> str:
    """Create a user and return an access token."""
    from models.otp import OTP
    from datetime import datetime, timedelta, timezone
    user_email = f"{role}_{uuid.uuid4().hex[:8]}@veritas.ai"
    user_data = {
        "name": f"{role.capitalize()} User",
        "email": user_email,
        "password": "securepassword123",
        "role": role,
    }
    db = TestingSessionLocal()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.add(OTP(email=user_data["email"], otp_code="123456", purpose="account_verification", expires_at=expires_at))
    db.commit()
    db.close()
    
    resp = client.post(REGISTER_URL, json=user_data, params={"otp_code": "123456"})
    assert resp.status_code == 201, f"Registration failed ({resp.status_code}): {resp.text}"
    
    # Force the role in the DB because create_user might override it
    db = TestingSessionLocal()
    from models.user import User
    user = db.query(User).filter(User.email == user_data["email"]).first()
    user.role = role
    db.commit()
    db.close()

    resp = client.post(
        LOGIN_URL,
        data={"username": user_data["email"], "password": user_data["password"]},
    )
    assert resp.status_code == 200, f"Login failed ({resp.status_code}): {resp.text}"
    data = resp.json()
    assert "access_token" in data, f"Missing access_token in response: {data}"
    return data["access_token"]


# ═══════════════════════════════════════
# opa_service unit tests (mocked HTTP)
# ═══════════════════════════════════════


@pytest.mark.asyncio
async def test_check_permission_allowed():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"result": True}
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()

    with patch("services.opa_service._get_client") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)
        from services.opa_service import check_permission

        assert await check_permission("partner", "documents", "delete_any") is True


@pytest.mark.asyncio
async def test_check_permission_denied():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"result": False}
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()

    with patch("services.opa_service._get_client") as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)
        from services.opa_service import check_permission

        assert await check_permission("paralegal", "documents", "delete_any") is False


@pytest.mark.asyncio
async def test_check_permission_fail_closed():
    """When OPA is unreachable and we are NOT in dev mode, the result should be deny."""
    with patch("services.opa_service._get_client") as mock_client, \
         patch("services.opa_service._is_dev_mode", return_value=False), \
         patch("services.opa_service._check_db_permission", return_value=None):
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            side_effect=Exception("connection refused")
        )
        from services.opa_service import check_permission

        assert await check_permission("partner", "documents", "upload") is False


@pytest.mark.asyncio
async def test_get_allowed_actions():
    fake_actions = [
        {"resource": "documents", "action": "upload"},
        {"resource": "documents", "action": "list_own"},
    ]
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"result": fake_actions}
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()

    with patch("services.opa_service._get_client") as mock_client, \
         patch("services.opa_service._is_dev_mode", return_value=False), \
         patch("services.opa_service._get_db_allowed_actions", return_value=None):
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_resp)
        from services.opa_service import get_allowed_actions

        result = await get_allowed_actions("paralegal")
        assert len(result) == 2
        assert result[0]["resource"] == "documents"


# ═══════════════════════════════════════
# Endpoint integration tests (OPA mocked)
# ═══════════════════════════════════════

def test_permissions_endpoint():
    """GET /auth/permissions returns role + permissions list."""
    token = _register_and_login("associate")

    fake_perms = [
        {"resource": "documents", "action": "upload"},
        {"resource": "documents", "action": "read_any"},
    ]
    with patch(
        "services.opa_service.get_allowed_actions",
        new_callable=AsyncMock,
        return_value=fake_perms,
    ):
        resp = client.get(
            "/api/auth/permissions",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "associate"
    assert len(data["permissions"]) == 2


def test_upload_allowed_by_opa():
    """Upload succeeds when OPA allows."""
    token = _register_and_login("associate")

    pdf = (
        b"%PDF-1.0\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\n"
        b"startxref\n190\n%%EOF"
    )

    with patch(
        "services.opa_service.check_permission",
        new_callable=AsyncMock,
        return_value=True,
    ):
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(pdf), "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 201


def test_upload_denied_by_opa():
    """Upload returns 403 when OPA denies (e.g. it_admin cannot upload)."""
    token = _register_and_login("it_admin")

    pdf = b"%PDF-1.0\n%%EOF"

    with patch(
        "services.opa_service.check_permission",
        new_callable=AsyncMock,
        return_value=False,
    ):
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(pdf), "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 403
    assert "permission denied" in resp.json()["detail"].lower()
