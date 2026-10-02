"""
Pydantic models for user registration, authentication, and profile responses.
"""

import re
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: str = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, max_length=100, description="Password (at least 6 characters)")
    role: Literal["USER", "ADMIN"] = Field(default="USER", description="Access role: USER or ADMIN")

    @field_validator("email")
    @classmethod
    def validate_email_address(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not re.match(EMAIL_REGEX, cleaned):
            raise ValueError("Invalid email address format (must be like user@example.com)")
        return cleaned

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
