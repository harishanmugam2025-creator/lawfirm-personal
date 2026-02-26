import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone

os.environ["TESTING"] = "true"

from api.main import app
from models.database import Base, get_db
from models.otp import OTP

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


client = TestClient(app)

REGISTER_URL = "/api/auth/register"
LOGIN_URL = "/api/auth/login"
ME_URL = "/api/auth/me"

TEST_USER = {
    "name": "Test User",
    "email": "testuser@veritas.ai",
    "password": "securepassword123",
}


def _register_and_login():
    """Helper: register a user and return the access token."""
    db = TestingSessionLocal()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.add(OTP(email=TEST_USER["email"], otp_code="123456", purpose="account_verification", expires_at=expires_at))
    db.commit()
    db.close()
    resp = client.post(REGISTER_URL, json=TEST_USER, params={"otp_code": "123456"})
    assert resp.status_code == 201, f"Registration failed ({resp.status_code}): {resp.text}"
    resp = client.post(LOGIN_URL, data={"username": TEST_USER["email"], "password": TEST_USER["password"]})
    assert resp.status_code == 200, f"Login failed ({resp.status_code}): {resp.text}"
    data = resp.json()
    assert "access_token" in data, f"Missing access_token in response: {data}"
    return data["access_token"]


# ---------- Registration Tests ----------

def test_register_first_user_is_it_admin():
    db = TestingSessionLocal()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.add(OTP(email=TEST_USER["email"], otp_code="123456", purpose="account_verification", expires_at=expires_at))
    db.commit()
    db.close()
    resp = client.post(REGISTER_URL, json=TEST_USER, params={"otp_code": "123456"})
    # Mocking OTP verification or just assuming it works for tests if it's bypassable?
    # Actually, repository needs OTP. I'll need to mock otp_repository or add a test entry.
    # For now, let's update assertions to expect 'it_admin' for first user.

    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "it_admin"
    assert data["email"] == TEST_USER["email"]
    assert data["name"] == TEST_USER["name"]


def test_register_subsequent_user_is_paralegal():
    db = TestingSessionLocal()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.add(OTP(email=TEST_USER["email"], otp_code="123456", purpose="account_verification", expires_at=expires_at))
    db.commit()

    # Register first user
    client.post(REGISTER_URL, json=TEST_USER, params={"otp_code": "123456"})

    # Register second user
    second_user = TEST_USER.copy()
    second_user["email"] = "second@veritas.ai"
    db.add(OTP(email=second_user["email"], otp_code="123456", purpose="account_verification", expires_at=expires_at))
    db.commit()
    db.close()
    resp = client.post(REGISTER_URL, json=second_user, params={"otp_code": "123456"})

    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "paralegal"


def test_register_duplicate_email():
    db = TestingSessionLocal()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.add(OTP(email=TEST_USER["email"], otp_code="123456", purpose="account_verification", expires_at=expires_at))
    db.commit()
    db.close()
    client.post(REGISTER_URL, json=TEST_USER, params={"otp_code": "123456"})

    # Add another OTP for the second attempt, but it should fail because email is taken
    db = TestingSessionLocal()
    db.query(OTP).filter(OTP.email == TEST_USER["email"]).delete()
    db.add(OTP(email=TEST_USER["email"], otp_code="654321", purpose="account_verification", expires_at=expires_at))
    db.commit()
    db.close()

    resp = client.post(REGISTER_URL, json=TEST_USER, params={"otp_code": "654321"})
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


# ---------- Login Tests ----------

def test_login_success():
    db = TestingSessionLocal()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.add(OTP(email=TEST_USER["email"], otp_code="123456", purpose="account_verification", expires_at=expires_at))
    db.commit()
    db.close()
    client.post(REGISTER_URL, json=TEST_USER, params={"otp_code": "123456"})
    resp = client.post(LOGIN_URL, data={"username": TEST_USER["email"], "password": TEST_USER["password"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    db = TestingSessionLocal()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.add(OTP(email=TEST_USER["email"], otp_code="123456", purpose="account_verification", expires_at=expires_at))
    db.commit()
    db.close()
    client.post(REGISTER_URL, json=TEST_USER, params={"otp_code": "123456"})
    resp = client.post(LOGIN_URL, data={"username": TEST_USER["email"], "password": "wrongpassword"})
    assert resp.status_code == 401


def test_login_nonexistent_user():
    resp = client.post(LOGIN_URL, data={"username": "nobody@veritas.ai", "password": "whatever"})
    assert resp.status_code == 401


# ---------- /auth/me Tests ----------

def test_me_authenticated():
    token = _register_and_login()
    resp = client.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == TEST_USER["email"]
    assert "role" in data


def test_me_no_token():
    resp = client.get(ME_URL)
    assert resp.status_code == 401


def test_me_invalid_token():
    resp = client.get(ME_URL, headers={"Authorization": "Bearer invalidtoken123"})
    assert resp.status_code == 401
