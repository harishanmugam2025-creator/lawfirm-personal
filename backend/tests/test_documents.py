import io
import os
from unittest.mock import AsyncMock, patch

os.environ["TESTING"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import app
from models.database import Base, get_db

# In-memory SQLite for tests
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
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Mock OPA to always allow (matches pre-OPA behaviour)
@pytest.fixture(autouse=True)
def mock_s3():
    with patch("services.document_service.s3_client") as mock_s3_client:
        yield mock_s3_client

@pytest.fixture(autouse=True)
def mock_opa():
    with patch(
        "services.opa_service.check_permission",
        new_callable=AsyncMock,
        return_value=True,
    ):
        yield


client = TestClient(app)

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
UPLOAD_URL = "/api/documents/upload"
LIST_URL = "/api/documents"

TEST_USER = {
    "name": "Doc User",
    "email": "docuser@veritas.ai",
    "password": "securepassword123",
    "role": "associate",
}


def _get_token():
    """Helper: register a user and return the access token."""
    from models.otp import OTP
    from datetime import datetime, timedelta, timezone
    db = TestingSessionLocal()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.add(OTP(email=TEST_USER["email"], otp_code="123456", purpose="account_verification", expires_at=expires_at))
    db.commit()
    db.close()
    client.post(REGISTER_URL, json=TEST_USER, params={"otp_code": "123456"})
    resp = client.post(LOGIN_URL, data={"username": TEST_USER["email"], "password": TEST_USER["password"]})
    return resp.json()["access_token"]


def _make_pdf_bytes():
    """Create a minimal valid PDF in memory."""
    # Minimal PDF 1.0 structure
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
    return pdf


# ---------- Upload Tests ----------

def test_upload_pdf_success():
    token = _get_token()
    pdf_bytes = _make_pdf_bytes()
    resp = client.post(
        UPLOAD_URL,
        files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["filename"] == "test.pdf"
    assert data["content_type"] == "application/pdf"
    assert "id" in data
    assert "created_at" in data


def test_upload_non_pdf_rejected():
    token = _get_token()
    resp = client.post(
        UPLOAD_URL,
        files={"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert "pdf" in resp.json()["detail"].lower()


def test_upload_no_auth():
    pdf_bytes = _make_pdf_bytes()
    resp = client.post(
        UPLOAD_URL,
        files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert resp.status_code == 401


# ---------- List Tests ----------

def test_list_documents_empty():
    token = _get_token()
    resp = client.get(LIST_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["documents"] == []
    assert data["total"] == 0


def test_list_documents_after_upload():
    token = _get_token()
    pdf_bytes = _make_pdf_bytes()
    client.post(
        UPLOAD_URL,
        files={"file": ("doc1.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.get(LIST_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["documents"][0]["filename"] == "doc1.pdf"


# ---------- Get Tests ----------

def test_get_document_by_id():
    token = _get_token()
    pdf_bytes = _make_pdf_bytes()
    upload_resp = client.post(
        UPLOAD_URL,
        files={"file": ("detail.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    doc_id = upload_resp.json()["id"]

    resp = client.get(f"{LIST_URL}/{doc_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["filename"] == "detail.pdf"


def test_get_nonexistent_document():
    token = _get_token()
    resp = client.get(f"{LIST_URL}/nonexistent-id", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


# ---------- Delete Tests ----------

def test_delete_document():
    token = _get_token()
    pdf_bytes = _make_pdf_bytes()
    upload_resp = client.post(
        UPLOAD_URL,
        files={"file": ("todelete.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    doc_id = upload_resp.json()["id"]

    resp = client.delete(f"{LIST_URL}/{doc_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204

    # Verify it's gone
    get_resp = client.get(f"{LIST_URL}/{doc_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 404


def test_delete_nonexistent_document():
    token = _get_token()
    resp = client.delete(f"{LIST_URL}/nonexistent-id", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404
