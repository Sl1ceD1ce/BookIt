import jwt
from datetime import datetime, timedelta, timezone
from constants import JWT_SECRET, JWT_ALGORITHM, JWT_EXP_HOURS
import helpers
import dataStore as ds


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


def register_user(user_data) -> dict:
    """Register a new user. Accepts Pydantic model directly."""

    # Check uniqueness
    if helpers.email_exists(user_data.email):
        raise ValueError("email already registered")
    if helpers.mobile_exists(user_data.mobile):
        raise ValueError("mobile number already registered")

    # Generate ID
    user_id = helpers.get_next_user_id()

    # Create user dict
    user = {
        "id": user_id,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "email": user_data.email,
        "mobile": user_data.mobile,
        "password": user_data.password,  # TODO: hash password
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
    token = create_jwt_token(user_id, user_data.email)

    return {
        "id": user_id,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "email": user_data.email,
        "mobile": user_data.mobile,
        "token": token,
        "message": "User registered successfully",
    }

def get_users(token: str) -> dict:

    decoded_token = decode_jwt_token(token)
    user_data = helpers.find_user_info(decoded_token)

    if not user_data:
        raise ValueError("user does not exist")
    
    return {
        "email": user_data["email"],
        "mobile": user_data["mobile"],
        "first_name": user_data["first_name"],
        "last_name": user_data["last_name"],
        "tutor": user_data["role"] == "tutor"
    }
