import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, String, DateTime, Boolean
from models.database import Base

class OTP(Base):
    __tablename__ = "otps"

    email = Column(String, primary_key=True, index=True)
    otp_code = Column(String, nullable=False)
    purpose = Column(String, primary_key=True, nullable=False) # e.g., "account_verification", "password_reset"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    is_verified = Column(Boolean, default=False)

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else datetime.now(timezone.utc) > self.expires_at
