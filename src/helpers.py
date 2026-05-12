import dataStore as ds
import jwt
from datetime import datetime, timedelta, timezone
from constants import JWT_SECRET, JWT_ALGORITHM, JWT_EXP_HOURS
import uuid
from fastapi import HTTPException


def create_jwt_token(user_id: str) -> str:
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
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def generate_id() -> str:
    """Generates a random id using uuid4"""
    return str(uuid.uuid4())


def email_exists(email: str) -> bool:
    data = ds.get_data()
    for user in data["users"]:
        if user["email"] == email:
            return True
    return False


def mobile_exists(mobile: str) -> bool:
    data = ds.get_data()
    for user in data["users"]:
        if user["mobile"] == mobile:
            return True
    return False


def find_user_info(decoded_token: dict) -> dict | None:
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
    data = ds.get_data()
    for lesson in data["lessons"]:
        if lesson_id == lesson["lesson_id"]:
            return lesson
    return None

def is_valid_datetime(string: str) -> bool:
    try: 
        datetime.fromisoformat(string)
        return True
    except ValueError:
        return False
    
def get_lessons() -> list:
    data = ds.get_data()
    return data["lessons"]

def check_lesson_time(user_data, lesson_data, lesson_id):
    existing_lessons = []
    for lesson in ds.get_data()["lessons"]:
        if lesson["tutor_id"] == user_data["id"]:
            existing_lessons.append(lesson)

    for lesson in existing_lessons:
        if lesson['lesson_id'] == lesson_id:
            continue

        existing_start = datetime.fromisoformat(lesson["start_time"])
        existing_end = datetime.fromisoformat(lesson["end_time"])

        if (datetime.fromisoformat(lesson_data["start_time"]) < existing_end and existing_start < datetime.fromisoformat(lesson_data["end_time"])):
            raise HTTPException(status_code=400, detail="Lesson overlaps with existing lesson")

def invalidate_token(token: str) -> None:
    data = ds.get_data()

    decoded = decode_jwt_token(token)
    data["invalidated_tokens"].append(
        {
            "token": token,
            "user_id": decoded["user_id"],
            "invalidated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
