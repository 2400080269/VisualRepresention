"""
Authentication router: Registration, Login, and Profile endpoints.
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database.models import User
from backend.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse
from backend.auth.password import hash_password, verify_password
from backend.auth.jwt import create_access_token
from backend.auth.dependencies import get_current_user
from backend.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Register New User")
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user account with hashed password and role assignment.
    """
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    if existing_user:
        if existing_user.username == user_in.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{user_in.username}' is already taken."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user_in.email}' is already registered."
            )

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=user_in.role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=TokenResponse, summary="User Login (Generate JWT)")
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates user credentials and issues a signed JSON Web Token.
    """
    user = db.query(User).filter(
        (User.username == credentials.username_or_email) | (User.email == credentials.username_or_email)
    ).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support."
        )

    # Issue JWT
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

@router.get("/me", response_model=UserResponse, summary="Get Current Authenticated Profile")
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the profile and role details of the authenticated caller.
    """
    return current_user
