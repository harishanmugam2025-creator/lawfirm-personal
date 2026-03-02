
import os
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from api.main import app
from models.database import Base, get_db

# Set TESTING environment variable before anything else
os.environ["TESTING"] = "true"

# Pre-import all models to ensure they are registered with Base.metadata
import models

# Use a single test database file
TEST_DATABASE_URL = "sqlite:///./test_veritas.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Enable SQLite foreign key support for the test engine
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

# Apply the override globally to the app
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    """
    Function-scoped fixture that ensures a clean database schema for every single test.
    """
    # Create all tables defined in Base.metadata
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables after the test
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """
    Provides a SQLAlchemy session directly to a test function if needed.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
