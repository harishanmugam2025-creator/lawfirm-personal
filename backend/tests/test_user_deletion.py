import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone

os.environ["TESTING"] = "true"

from api.main import app
from models.database import Base, get_db
from models.user import User
from models.document import Document
from models.legal_research import SavedCase, LegalCase
from models.timesheet import Timesheet
from models.lawfirm_case import LawfirmCase
from models.otp import OTP
from services.auth_service import hash_password

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test_deletion.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

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

def test_delete_user_cascades():
    db = TestingSessionLocal()
    
    # 1. Create IT Admin
    admin_pwd = "adminpassword"
    admin_email = "admin@veritas.ai"
    admin = User(
        name="Admin",
        email=admin_email,
        hashed_password=hash_password(admin_pwd),
        role="it_admin"
    )
    db.add(admin)
    db.commit()
    
    # 2. Create Target User (Paralegal)
    user_pwd = "userpassword"
    target_email = "target@veritas.ai"
    target_user = User(
        name="Target User",
        email=target_email,
        hashed_password=hash_password(user_pwd),
        role="paralegal"
    )
    db.add(target_user)
    db.commit()
    target_id = target_user.id
    
    # 3. Create dependent records for Target User
    legal_case = LegalCase(title="Test Case", court="Test Court", jurisdiction="Test J", year=2024, regulation="Test R", summary="S", full_text="FT")
    db.add(legal_case)
    db.commit()
    
    saved_case = SavedCase(user_id=target_id, case_id=legal_case.id)
    db.add(saved_case)
    
    doc = Document(filename="test.pdf", size_bytes=100, disk_path="/tmp/test.pdf", uploaded_by=target_id)
    db.add(doc)
    
    db.commit()
    
    # Verify records exist
    assert db.query(User).filter(User.id == target_id).first() is not None
    assert db.query(SavedCase).filter(SavedCase.user_id == target_id).first() is not None
    assert db.query(Document).filter(Document.uploaded_by == target_id).first() is not None
    
    db.close()
    
    # 4. Login as Admin
    login_resp = client.post("/api/auth/login", data={"username": admin_email, "password": admin_pwd})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    
    # 5. Delete Target User
    delete_resp = client.delete(f"/api/users/{target_id}", headers={"Authorization": f"Bearer {token}"})
    assert delete_resp.status_code == 204
    
    # 6. Verify records are gone
    db = TestingSessionLocal()
    assert db.query(User).filter(User.id == target_id).first() is None
    assert db.query(SavedCase).filter(SavedCase.user_id == target_id).first() is None
    assert db.query(Document).filter(Document.uploaded_by == target_id).first() is None
    db.close()
