from datetime import datetime, timezone
from sqlalchemy import delete, select, update
import helpers
from fastapi import HTTPException
from sqlalchemy.orm import Session
from database import User, Lesson


def register_user(user_data, db: Session) -> dict:
    """Register a new user. Accepts Pydantic model directly."""

    # Check uniqueness
    if helpers.email_exists(user_data.email, db):
        raise ValueError("email already registered")
    if helpers.mobile_exists(user_data.mobile, db):
        raise ValueError("mobile number already registered")

    # Generate ID
    user_id = helpers.generate_id()

    # Create user dict
    user = User(
        id=user_id,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        mobile=user_data.mobile,
        password=user_data.password,
        role="tutor" if user_data.tutor else "student"
    )

    # Add user directly to datastore
    db.add(user)
    db.commit()

    # Create JWT
    token = helpers.create_jwt_token(user_id)

    return {
        "id": user_id,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "email": user_data.email,
        "mobile": user_data.mobile,
        "token": token,
        "message": "User registered successfully",
    }


def login_user(login_data, db: Session) -> dict:
    user = db.execute(select(User).where(User.password == login_data.password, User.email == login_data.email)).scalar_one_or_none()

    if not user:
        raise ValueError("incorrect username or password")

    token = helpers.create_jwt_token(user.id)

    return {"token": token}


def get_users(token: str, db: Session) -> dict:
    if helpers.is_token_blacklisted(token, db):
        raise ValueError("token is invalid")

    decoded_token = helpers.decode_jwt_token(token)
    user_data = helpers.find_user_info(decoded_token, db)

    if not user_data:
        raise ValueError("user does not exist")

    return {
        "email": user_data.email,
        "mobile": user_data.mobile,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "tutor": user_data.role == "tutor",
    }


def logout_user(token: str, db: Session) -> dict:
    """Invalidate a token by adding it to blacklist"""
    if helpers.is_token_blacklisted(token, db):
        raise ValueError("token is invalid")

    # Invalidate the token
    helpers.invalidate_token(token, db)

    return {"message": "Logged out successfully"}
   


def delete_user(token: str, db: Session) -> dict:
    """Deletes a user from the system including the associated lessons if the user is a tutor"""
    if helpers.is_token_blacklisted(token, db):
        raise HTTPException(status_code=401, detail="Token is invalid")

    decoded_token = helpers.decode_jwt_token(token)
    user_data = helpers.find_user_info(decoded_token, db)

    if not user_data:
        raise HTTPException(status_code=401, detail="User does not exist")

    # If user is a tutor, delete all their lessons
    if user_data.role == "tutor":
        lessons = db.execute(delete(Lesson).where(Lesson.tutor_id == user_data.id))
    else:  # Student
        # Remove student from all lessons they're enrolled in
        lessons = db.execute(update(Lesson).where(Lesson.assigned_student_id == user_data.id).values(assigned_student_id=None, available=True))

    # Remove the user from the datastore
    db.delete(user_data)

    # Invalidate the token
    helpers.invalidate_token(token, db)
    db.commit()

    return {"message": "User deleted successfully"}
