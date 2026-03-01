from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config import settings
from repositories import user_repository, otp_repository
from schemas.auth import UserCreate, Token, ResetPassword
from services.email_service import email_service


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def register_user(db: Session, user_data: UserCreate, otp_code: str):
    """Verify OTP and register a new user."""
    is_valid = otp_repository.verify_otp(db, user_data.email, otp_code, "account_verification")
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code",
        )
    
    existing = user_repository.get_user_by_email(db, user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    hashed = hash_password(user_data.password)
    return user_repository.create_user(db, user_data, hashed)


def send_registration_otp(db: Session, email: str):
    """Send OTP for account verification."""
    existing = user_repository.get_user_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    otp_code = otp_repository.generate_otp(db, email, "account_verification")
    success = email_service.send_otp_email(email, otp_code, "account_verification")
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later or check system logs."
        )
    return True


def authenticate_user(db: Session, email: str, password: str) -> Token:
    """Authenticate user and return a JWT. Raises 401 on failure."""
    from services import audit_service

    user = user_repository.get_user_by_email(db, email)
    
    # 1. Validate credentials
    if not user or not verify_password(password, user.hashed_password):
        audit_service.log_action(
            db,
            user_id="anonymous",
            resource="auth",
            action="login_failure",
            module="Authentication",
            metadata={"email": email, "reason": "invalid_credentials"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
        
    # 2. Check account status
    if not user.is_active:
        audit_service.log_action(
            db,
            user=user,
            resource="auth",
            action="login_blocked_inactive",
            module="Authentication",
            metadata={"email": email, "reason": "account_inactive"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact your administrator.",
        )
    
    # 3. Successful login
    audit_service.log_action(
        db,
        user=user,
        resource="auth",
        action="login_success",
        module="Authentication",
        metadata={"email": email}
    )

    token = create_access_token({"sub": user.id, "role": user.role})
    return Token(access_token=token)


def forgot_password(db: Session, email: str):
    """Generate OTP and send email for password reset."""
    user = user_repository.get_user_by_email(db, email)
    if not user:
        # For security, don't reveal if user exists. Just return.
        return True
    
    otp_code = otp_repository.generate_otp(db, email, "password_reset")
    success = email_service.send_otp_email(email, otp_code, "password_reset")
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send reset email. Please try again later."
        )
    return True


def reset_password(db: Session, data: ResetPassword):
    """Verify OTP and update user password."""
    is_valid = otp_repository.verify_otp(db, data.email, data.otp_code, "password_reset")
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code",
        )
    
    user = user_repository.get_user_by_email(db, data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    hashed = hash_password(data.new_password)
    user_repository.update_user(db, user, hashed_password=hashed)
    return True
