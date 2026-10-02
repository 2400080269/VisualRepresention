"""
Pydantic models for user registration, authentication, and profile responses.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, max_length=100, description="Password (at least 6 characters)")
    role: Literal["USER", "ADMIN"] = Field(default="USER", description="Access role: USER or ADMIN")

class UserLogin(BaseModel):
    username_or_email: str = Field(..., description="Registered username or email")
    password: str = Field(..., description="Account password")

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    expires_in_minutes: int
