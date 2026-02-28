from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_current_user

from models.database import get_db
from models.user import User
from schemas.auth import UserCreate, UserResponse, Token, ForgotPasswordRequest, ResetPassword
from services import auth_service, opa_service, audit_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginJSON(BaseModel):
    email: str
    password: str



@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, otp_code: str, db: Session = Depends(get_db)):
    """Register a new user account with OTP verification."""
    user = auth_service.register_user(db, user_data, otp_code)
    
    audit_service.log_action(
        db,
        user=user,
        resource="auth",
        action="register",
        resource_id=user.id,
        metadata={"email": user.email, "role": user.role}
    )
    return user


@router.post("/registration-otp")
def send_registration_otp(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send an OTP code to verify email before registration."""
    auth_service.send_registration_otp(db, data.email)
    return {"message": "OTP sent successfully."}


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate and receive a JWT access token.

    Uses OAuth2 form: 'username' field = email, 'password' field = password.
    """
    return auth_service.authenticate_user(db, form_data.username, form_data.password)


@router.post("/login-json", response_model=Token)
def login_json(payload: LoginJSON, db: Session = Depends(get_db)):
    """Authenticate with JSON body instead of form data."""
    return auth_service.authenticate_user(db, payload.email, payload.password)



@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return current_user


@router.get("/permissions")
async def get_permissions(current_user: User = Depends(get_current_user)):
    """Return the list of allowed {resource, action} pairs for the current user.

    The frontend uses this to conditionally show/hide UI elements.
    """
    actions = await opa_service.get_allowed_actions(current_user.role)
    return {"role": current_user.role, "permissions": actions}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request a password reset OTP."""
    auth_service.forgot_password(db, data.email)
    
    # We log this as a generic auth attempt for security
    audit_service.log_action(
        db,
        user=None,  # We don't have a login session here, but let's see if we can log a system-level event
        resource="auth",
        action="forgot_password",
        metadata={"email": data.email}
    )
    return {"message": "If the email is registered, you will receive an OTP code."}


@router.get("/diag/email")
def diag_email():
    """Diagnostic endpoint to check email service configuration."""
    from services.email_service import email_service
    from config import settings
    
    api_key = settings.SENDGRID_API_KEY
    is_valid_format = api_key.startswith("SG.") if api_key else False
    
    return {
        "demo_mode": email_service.demo_mode,
        "debug_mode": settings.DEBUG_MODE,
        "from_email": settings.SENDGRID_FROM_EMAIL,
        "api_key_valid_format": is_valid_format,
        "api_key_prefix": api_key[:7] + "..." if api_key else "None"
    }

@router.post("/reset-password")
def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    """Reset password using OTP."""
    auth_service.reset_password(db, data)
    
    # For reset, we can find the user to log who it was
    user = auth_service.user_repository.get_user_by_email(db, data.email)
    if user:
        audit_service.log_action(
            db,
            user=user,
            resource="auth",
            action="reset_password",
            resource_id=user.id,
            metadata={"email": user.email}
        )
    return {"message": "Password reset successfully."}
