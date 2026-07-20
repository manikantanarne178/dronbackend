from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from jose import jwt, JWTError

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
)

from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):

    email_exists = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if email_exists:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    username_exists = (
        db.query(User)
        .filter(User.username == request.username)
        .first()
    )

    if username_exists:
        raise HTTPException(
            status_code=400,
            detail="Username already exists",
        )

    user = User(
        username=request.username,
        email=request.email,
        password=hash_password(request.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "message": "User registered successfully",
    }


@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):

    user = (
        db.query(User)
        .filter(User.email == request.email)
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
    }
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


@router.get("/me")
def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = int(payload["sub"])

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid Token",
        )

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }