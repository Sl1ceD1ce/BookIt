"""
Utility helper functions for authentication, validation, and database access.

This module provides reusable helper functions for:
- JWT token creation and decoding
- UUID generation
- User and lesson database lookups
- Token invalidation checks
- Datetime validation
- Lesson scheduling conflict detection

The functions in this module are primarily used by FastAPI route
handlers and service-layer logic throughout the application.
"""

from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
import jwt

# pylint: disable=import-error
from fastapi import HTTPException
from database import User, InvalidatedToken, Lesson

from constants import JWT_SECRET, JWT_ALGORITHM, JWT_EXP_HOURS


def create_jwt_token(user_id: str) -> str:
    """Creates a jwt token"""
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXP_HOURS)
    payload = {"user_id": user_id, "exp": expiration}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_jwt_token(token: str) -> dict:
    """
    Docstring for decode_jwt_token

    :param token: A JWT token
    :type token: str
    :return: A dictionary containing user_id and exp (expiration date)
    :rtype: dict
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise ValueError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError("Invalid token") from exc


def generate_id() -> str:
    """Generates a random id using uuid4"""
    return str(uuid.uuid4())


def email_exists(email: str, db: Session) -> bool:
    """Check if an email already exists."""
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none() is not None


def mobile_exists(mobile: str, db: Session) -> bool:
    """Check if a mobile number already exists."""
    return db.execute(select(User).where(User.mobile == mobile)).scalar_one_or_none() is not None


def find_user_info(decoded_token: dict, db: Session):
    """Retrieve a user from a decoded token."""
    return db.execute(select(User).where(User.id == decoded_token["user_id"])).scalar_one_or_none()


def is_token_blacklisted(token: str, db: Session) -> bool:
    """Check if token has been invalidated"""
    return db.execute(
        select(InvalidatedToken)
        .where(InvalidatedToken.token == token)
        ).scalar_one_or_none() is not None


def find_lesson_info(lesson_id: str, db: Session):
    """Retrieve lesson information by lesson ID."""
    return db.execute(select(Lesson).where(Lesson.id == lesson_id)).scalar_one_or_none()


def is_valid_datetime(string: str) -> bool:
    """checks if the datetime si valid"""
    try:
        datetime.fromisoformat(string)
        return True
    except ValueError:
        return False

def get_lessons(db) -> list:
    """Retrieve all lessons from the database."""
    stmt = select(Lesson)
    result = db.execute(stmt)
    return result.scalars().all()

def check_lesson_time(user_data, lesson_data, lesson_id, db):
    """Check for overlapping lessons for a tutor."""
    new_start = datetime.fromisoformat(lesson_data["start_time"])
    new_end = datetime.fromisoformat(lesson_data["end_time"])

    stmt = select(Lesson).where(
        Lesson.tutor_id == user_data.id,
        Lesson.id != lesson_id,
        and_(
            new_start.isoformat() < Lesson.end_time,
            Lesson.start_time < new_end.isoformat()
        )
    )

    conflict = db.execute(stmt).scalar_one_or_none()

    if conflict:
        raise HTTPException(
            status_code=400,
            detail="Lesson overlaps with existing lesson"
        )

def invalidate_token(token: str, db: Session) -> None:
    """Invalidate a JWT token."""
    decoded = decode_jwt_token(token)
    invalid_token = InvalidatedToken(
        token=token,
        user_id=decoded["user_id"],
        invalidated_at=datetime.now(timezone.utc).isoformat()
    )
    db.add(invalid_token)
    db.commit()
