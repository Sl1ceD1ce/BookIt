from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from datetime import datetime
from typing import Optional


class UserRegister(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=30)
    last_name: str = Field(..., min_length=1, max_length=30)
    email: EmailStr = Field(..., max_length=50)
    password: str = Field(..., min_length=1, max_length=30)
    mobile: str
    tutor: bool

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("name cannot be empty or just whitespace")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not re.match(r"^[A-Za-z0-9_]+$", v):
            raise ValueError(
                "password can only contain letters, numbers, and underscores"
            )
        return v

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        mobile_str = str(v).replace(" ", "").replace("-", "")
        if not re.match(r"^04\d{8}$", mobile_str):
            raise ValueError("invalid mobile number format")
        return mobile_str


class UserResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    mobile: str
    token: str
    message: str


class UserLogin(BaseModel):
    email: EmailStr = Field(..., max_length=50)
    password: str = Field(..., min_length=1, max_length=30)


class UserLoginResponse(BaseModel):
    token: str


class LessonCreate(BaseModel):
    start_time: str
    end_time: str
    subject: str


class LessonResponse(BaseModel):
    lesson_id: str
    start_time: str
    end_time: str
    duration: int
    subject: str
    tutor_id: str
    assigned_student_id: Optional[str] = None
    available: bool


class LessonUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    subject: Optional[str] = None
    assigned_student_id: Optional[str] = None
    available: Optional[bool] = None
