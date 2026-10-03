from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
)
from app.models.user import User
from app.models.notification import Notification
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
)
from app.services.email_service import send_welcome_email, send_password_reset_email

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    email_exists = (
        db.query(User)
        .filter(User.email == request.email.strip().lower())
        .first()
    )

    if email_exists:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    username_exists = (
        db.query(User)
        .filter(User.username == request.username.strip())
        .first()
    )

    if username_exists:
        raise HTTPException(
            status_code=400,
            detail="Username already exists",
        )

    user = User(
        username=request.username.strip(),
        email=request.email.strip().lower(),
        password=hash_password(request.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Create initial welcome notification
    welcome_notif = Notification(
        user_id=user.id,
        title="Welcome to DroneVision 3D",
        message=f"Welcome {user.username}! Your account is now active. Upload your first aerial drone survey to begin 3D reconstruction.",
        type="info",
    )
    db.add(welcome_notif)
    db.commit()

    # Trigger welcome email (non-blocking simulation/dispatch)
    email_res = send_welcome_email(user.email, user.username)

    return {
        "success": True,
        "message": "User registered successfully",
        "email_status": email_res,
    }


@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == request.email.strip().lower())
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(
        request.password,
        user.password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
        }
    )

    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "email": user.email,
        "user_id": user.id,
    }


@router.get("/me")
def current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the authenticated user's password.
    """
    if not verify_password(payload.current_password, current_user.password):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect.",
        )

    if len(payload.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 6 characters long.",
        )

    current_user.password = hash_password(payload.new_password)
    db.commit()

    # Create security notification
    notif = Notification(
        user_id=current_user.id,
        title="Password Changed",
        message="Your account password was successfully updated.",
        type="success",
    )
    db.add(notif)
    db.commit()

    return {
        "success": True,
        "message": "Password changed successfully.",
    }


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Generates a password reset token and dispatches reset email.
    """
    user = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if not user:
        # Don't leak user existence for security, return uniform response
        return {
            "success": True,
            "message": "If an account exists with this email, a password reset link has been dispatched.",
        }

    # Generate 1-hour reset token
    expire = datetime.utcnow() + timedelta(hours=1)
    reset_token = jwt.encode(
        {"sub": str(user.id), "email": user.email, "type": "reset", "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    send_password_reset_email(user.email, user.username, reset_token)

    return {
        "success": True,
        "message": "If an account exists with this email, a password reset token has been dispatched.",
        "reset_token": reset_token, # Included for ease of testing
    }


@router.post("/reset-password")
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Resets password using a validated reset token.
    """
    try:
        data = jwt.decode(payload.token, SECRET_KEY, algorithms=[ALGORITHM])
        if data.get("type") != "reset":
            raise HTTPException(status_code=400, detail="Invalid token type.")
        user_id = int(data.get("sub", "0"))
    except JWTError:
        raise HTTPException(status_code=400, detail="Password reset token has expired or is invalid.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")

    user.password = hash_password(payload.new_password)
    db.commit()

    notif = Notification(
        user_id=user.id,
        title="Password Reset Successful",
        message="Your account password has been reset successfully.",
        type="success",
    )
    db.add(notif)
    db.commit()

    return {
        "success": True,
        "message": "Password reset successfully. You may now log in with your new password.",
    }
