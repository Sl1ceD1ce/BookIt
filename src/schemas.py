"""Pydantic schemas for BookIt API validation and serialization."""

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    """Schema for user registration request."""

    first_name: str = Field(..., min_length=1, max_length=30)
    last_name: str = Field(..., min_length=1, max_length=30)
    email: EmailStr = Field(..., max_length=50)
    password: str = Field(..., min_length=8, max_length=30)
    mobile: str
    tutor: bool

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validates name fields - checks for empty strings and valid characters."""
        if not v.strip():
            raise ValueError("name cannot be empty or just whitespace")
        if not re.match(r"^[A-Za-z\- ]+$", v):
            raise ValueError(
                "Name can only contain alphabetical characters and hyphens"
            )
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validates password - requires at least one number and one special character."""
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain numbers")
        if not re.search(r"[^a-zA-Z0-9]", v):
            raise ValueError("Password must contain non-alphanumeric characters")
        return v

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        """Validates mobile number - must be valid Australian format (04XXXXXXXX)."""
        mobile_str: str = str(v).replace(" ", "").replace("-", "")
        if not re.match(r"^04\d{8}$", mobile_str):
            raise ValueError("invalid mobile number format")
        return mobile_str


class UserResponse(BaseModel):
    """Schema for user registration/login response."""

    id: str
    first_name: str
    last_name: str
    email: str
    mobile: str
    token: str
    message: str


class UserLogin(BaseModel):
    """Schema for user login request."""

    email: EmailStr = Field(..., max_length=50)
    password: str = Field(..., min_length=1, max_length=30)


class UserLoginResponse(BaseModel):
    """Schema for user login response."""

    token: str


class LessonCreate(BaseModel):
    """Schema for lesson creation request."""

    start_time: str
    end_time: str
    subject: str


class LessonResponse(BaseModel):
    """Schema for lesson response - used when retrieving lessons."""

    lesson_id: str
    start_time: str
    end_time: str
    duration: int
    subject: str
    tutor_id: str
    assigned_student_id: Optional[str] = None
    available: bool


class LessonUpdate(BaseModel):
    """Schema for lesson update request - all fields are optional."""

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    subject: Optional[str] = None
    assigned_student_id: Optional[str] = None
    available: Optional[bool] = None
