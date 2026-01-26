import dataStore as ds
import jwt
from datetime import datetime, timedelta, timezone
from constants import JWT_SECRET, JWT_ALGORITHM, JWT_EXP_HOURS
import uuid

def create_jwt_token(user_id: str, email: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXP_HOURS)
    payload = {"user_id": user_id, "email": email, "exp": expiration}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_jwt_token(token: str) -> dict:
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