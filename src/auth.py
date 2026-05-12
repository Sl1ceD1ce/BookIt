"""User authentication module handling registration, login, and token management."""

import helpers
import data_store as ds
from schemas import UserRegister, UserLogin


def register_user(user_data: UserRegister) -> dict:
    """Register a new user. Accepts Pydantic model directly."""
    # Check uniqueness
    if helpers.email_exists(user_data.email):
        raise ValueError("email already registered")
    if helpers.mobile_exists(user_data.mobile):
        raise ValueError("mobile number already registered")

    # Generate ID
    user_id = helpers.generate_id()

    # Create user dict
    user = {
        "id": user_id,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "email": user_data.email,
        "mobile": user_data.mobile,
        "password": user_data.password,  # hash password
        "role": "tutor" if user_data.tutor else "student",
        "payment_schedule": {},
        "availability": [],
        "enrolled_lessons": [],
    }

    # Role-specific fields
    if user_data.tutor:
        user.update(
            {
                "about_me": "",
                "bank_details": {},
                "tutor_rates": {},
                "lesson_preferences": {},
                "student_ids": [],
            }
        )
    else:
        user.update({"tutor_id": None})

    # Add user directly to datastore
    ds.get_data()["users"].append(user)

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


def login_user(login_data: UserLogin) -> dict:
    """Authenticate user credentials and return JWT token."""
    data = ds.get_data()

    user = None
    for u in data["users"]:
        if u["password"] == login_data.password and u["email"] == login_data.email:
            user = u

    if not user:
        raise ValueError("incorrect username or password")

    token = helpers.create_jwt_token(user["id"])

    return {"token": token}


def get_users(token: str) -> dict:
    """Retrieve authenticated user information from token."""
    user_data = helpers.validate_and_get_user(token)

    return {
        "email": user_data["email"],
        "mobile": user_data["mobile"],
        "first_name": user_data["first_name"],
        "last_name": user_data["last_name"],
        "tutor": user_data["role"] == "tutor",
    }


def logout_user(token: str) -> dict:
    """Invalidate a token by adding it to blacklist"""
    if helpers.is_token_blacklisted(token):
        raise ValueError("token is invalid")

    # Invalidate the token
    helpers.invalidate_token(token)

    return {"message": "Logged out successfully"}


def delete_user(token: str) -> dict:
    """Deletes a user from the system including the associated lessons if the user is a tutor"""
    user_data = helpers.validate_and_get_user(token)

    # If user is a tutor, delete all their lessons
    if user_data["role"] == "tutor":
        lessons = ds.get_data()["lessons"]
        ds.get_data()["lessons"] = [
            lesson for lesson in lessons if lesson["tutor_id"] != user_data["id"]
        ]
    else:  # Student
        # Remove student from all lessons they're enrolled in
        for lesson in ds.get_data()["lessons"]:
            if (
                lesson.get("student_id") == user_data["id"]
                or lesson.get("student_email") == user_data["email"]
            ):
                lesson["student_id"] = None
                lesson["student_email"] = None
                lesson["status"] = "Available"

    # Remove the user from the datastore
    users = ds.get_data()["users"]
    ds.get_data()["users"] = [user for user in users if user["id"] != user_data["id"]]

    # Invalidate the token
    helpers.invalidate_token(token)

    return {"message": "User deleted successfully"}
