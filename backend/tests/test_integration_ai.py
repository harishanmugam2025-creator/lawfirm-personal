import io
import json
import os

os.environ["TESTING"] = "true"

import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import app
from models.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///./test_veritas.db"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def mock_s3():
    with patch("services.document_service.s3_client") as mock_s3_client:
        yield mock_s3_client


@pytest.fixture(autouse=True)
def mock_opa():
    with patch("services.opa_service.check_permission", new_callable=AsyncMock, return_value=True):
        yield


@pytest.mark.asyncio
async def test_end_to_end_ai_analysis():
    """Validates the full Analysis persistence and Reasoning Path flow."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # 1. Start application with TestClient
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 1. Register a partner user and an it_admin user
        partner_data = {
            "name": "Partner User",
            "email": "partner@veritas.ai",
            "password": "securepassword",
            "role": "partner"
        }
        admin_data = {
            "name": "Admin User",
            "email": "admin@veritas.ai",
            "password": "securepassword",
            "role": "it_admin"
        }

        # Mock OTP
        from models.otp import OTP
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        engine = create_engine("sqlite:///./test_veritas.db", connect_args={"check_same_thread": False})
        TestingSessionLocal2 = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        from datetime import datetime, timedelta, timezone
        db = TestingSessionLocal2()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        db.add(OTP(
            email=partner_data["email"],
            otp_code="123456",
            purpose="account_verification",
            expires_at=expires_at
        ))
        db.add(OTP(
            email=admin_data["email"],
            otp_code="123456",
            purpose="account_verification",
            expires_at=expires_at
        ))
        db.commit()
        db.close()

        await client.post("/api/auth/register", json=partner_data, params={"otp_code": "123456"})
        await client.post("/api/auth/register", json=admin_data, params={"otp_code": "123456"})

        # 2. Login to get both tokens
        p_resp = await client.post(
            "/api/auth/login",
            data={"username": partner_data["email"], "password": partner_data["password"]}
        )
        assert p_resp.status_code == 200, f"Login failed: {p_resp.text}"
        partner_token = p_resp.json()["access_token"]
        partner_headers = {"Authorization": f"Bearer {partner_token}"}

        a_resp = await client.post(
            "/api/auth/login",
            data={"username": admin_data["email"], "password": admin_data["password"]}
        )
        assert a_resp.status_code == 200, f"Login failed: {a_resp.text}"
        admin_token = a_resp.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 3. Upload a Document
        dummy_pdf = io.BytesIO(
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
            b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
            b"0000000058 00000 n \n0000000115 00000 n \n"
            b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF"
        )
        files = {"file": ("test_doc.pdf", dummy_pdf, "application/pdf")}

        with patch("services.document_service.pdfplumber.open", side_effect=Exception("mocked")):
            doc_resp = await client.post("/api/documents/upload", files=files, headers=partner_headers)

        assert doc_resp.status_code == 201
        doc_id = doc_resp.json()["id"]

        # 4. Create an active Prompt Version
        prompt_data = {
            "analysis_type": "gdpr",
            "version": "v1.0.0",
            "system_prompt": "You are a legal AI. Analyze for GDPR compliance.",
            "is_active": True
        }
        prompt_resp = await client.post("/api/prompts", json=prompt_data, headers=admin_headers)
        assert prompt_resp.status_code == 201

        # 5. Analyze the document (will gracefully degrade since Ollama is offline)
        analyze_req = {
            "document_id": doc_id,
            "analysis_type": "gdpr"
        }
        analyze_resp = await client.post("/api/analyze", json=analyze_req, headers=partner_headers)
        assert analyze_resp.status_code == 201

        result = analyze_resp.json()
        print("\n✅ Verification Successful! Reasoning Path:")
        print(json.dumps({
            "rules_triggered": result["rules_triggered"],
            "confidence_score": result["confidence_score"],
            "source_text": result["source_text"],
            "latency_seconds": result["latency_seconds"]
        }, indent=2))

        # Assert the formatting matches the governance requirements
        assert "rules_triggered" in result
        assert "confidence_score" in result
        assert "source_text" in result
        assert "latency_seconds" in result
