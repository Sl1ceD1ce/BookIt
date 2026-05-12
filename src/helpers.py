from sqlalchemy import select
from sqlalchemy.orm import Session, and_
import jwt
from datetime import datetime, timedelta, timezone
from constants import JWT_SECRET, JWT_ALGORITHM, JWT_EXP_HOURS
import uuid
from fastapi import HTTPException
from database import User, InvalidatedToken, Lesson


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


def email_exists(email: str, db: Session) -> bool:
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none() is not None


def mobile_exists(mobile: str, db: Session) -> bool:
    return db.execute(select(User).where(User.mobile == mobile)).scalar_one_or_none() is not None


def find_user_info(decoded_token: dict, db: Session):
    return db.execute(select(User).where(User.id == decoded_token["user_id"])).scalar_one_or_none()


def is_token_blacklisted(token: str, db: Session) -> bool:
    """Check if token has been invalidated"""
    return db.execute(select(InvalidatedToken).where(InvalidatedToken.token == token)).scalar_one_or_none() is not None


def find_lesson_info(lesson_id: str, db: Session):
    return db.execute(Lesson.select(Lesson.lesson_id == lesson_id)).scalar_one_or_none()

def is_valid_datetime(string: str) -> bool:
    try: 
        datetime.fromisoformat(string)
        return True
    except ValueError:
        return False
    
def get_lessons(db) -> list:
    stmt = select(Lesson)
    result = db.execute(stmt)
    return result.scalars().all()

def check_lesson_time(user_data, lesson_data, lesson_id, db):
    new_start = datetime.fromisoformat(lesson_data["start_time"])
    new_end = datetime.fromisoformat(lesson_data["end_time"])

    stmt = select(Lesson).where(
        Lesson.tutor_id == user_data["id"],
        Lesson.id != lesson_id,
        and_(
            new_start < Lesson.end_time,
            Lesson.start_time < new_end
        )
    )

    conflict = db.execute(stmt).scalar_one_or_none()

    if conflict:
        raise HTTPException(
            status_code=400,
            detail="Lesson overlaps with existing lesson"
        )

def invalidate_token(token: str, db: Session) -> None:
    decoded = decode_jwt_token(token)
    invalid_token = InvalidatedToken(token=token, user_id=decoded["user_id"], invalidated_at=datetime.now(timezone.utc).isoformat())
    db.add(invalid_token)
    db.commit()
