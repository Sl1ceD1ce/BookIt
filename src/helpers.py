"""Module containing all helpers"""

import uuid
from datetime import datetime, timedelta, timezone

# pylint: disable=import-error
from fastapi import HTTPException
import jwt

import data_store as ds
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


def email_exists(email: str) -> bool:
    """checks if the given email already exists"""
    data = ds.get_data()
    for user in data["users"]:
        if user["email"] == email:
            return True
    return False


def mobile_exists(mobile: str) -> bool:
    """checks if the given mobile already exists"""
    data = ds.get_data()
    for user in data["users"]:
        if user["mobile"] == mobile:
            return True
    return False


def find_user_info(decoded_token: dict) -> dict | None:
    """finds a users info for a given token"""
    data = ds.get_data()
    for user in data["users"]:
        if decoded_token["user_id"] == user["id"]:
            return user
    return None


def is_token_blacklisted(token: str) -> bool:
    """Check if token has been invalidated"""
    data = ds.get_data()
    for entry in data["invalidated_tokens"]:
        if entry["token"] == token:
            return True
    return False


def find_lesson_info(lesson_id: str) -> dict | None:
    """finds the info for a gien lessonid"""
    data = ds.get_data()
    for lesson in data["lessons"]:
        if lesson_id == lesson["lesson_id"]:
            return lesson
    return None


def is_valid_datetime(string: str) -> bool:
    """checks if the datetime si valid"""
    try:
        datetime.fromisoformat(string)
        return True
    except ValueError:
        return False


def get_lessons() -> list:
    """gets all lessons from data"""
    data = ds.get_data()
    return data["lessons"]


def check_lesson_time(user_data, lesson_data, lesson_id):
    """Checks that a lesson time doesn't overlap with another lesson"""
    existing_lessons = []
    for lesson in ds.get_data()["lessons"]:
        if lesson["tutor_id"] == user_data["id"]:
            existing_lessons.append(lesson)

    for lesson in existing_lessons:
        if lesson["lesson_id"] == lesson_id:
            continue

        existing_start = datetime.fromisoformat(lesson["start_time"])
        existing_end = datetime.fromisoformat(lesson["end_time"])

        if datetime.fromisoformat(
            lesson_data["start_time"]
        ) < existing_end and existing_start < datetime.fromisoformat(
            lesson_data["end_time"]
        ):
            raise HTTPException(
                status_code=400, detail="Lesson overlaps with existing lesson"
            )


def invalidate_token(token: str) -> None:
    """Invalidates a users token from the database"""
    data = ds.get_data()

    decoded = decode_jwt_token(token)
    data["invalidated_tokens"].append(
        {
            "token": token,
            "user_id": decoded["user_id"],
            "invalidated_at": datetime.now(timezone.utc).isoformat(),
        }
    )


def validate_and_get_user(token: str) -> dict:
    """Validate a token and retrieve the associated user."""
    if is_token_blacklisted(token):
        raise ValueError("token is invalid")

    decoded_token = decode_jwt_token(token)
    user_data = find_user_info(decoded_token)

    if not user_data:
        raise ValueError("user does not exist")

    return user_data
