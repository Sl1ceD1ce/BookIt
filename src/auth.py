import jwt
from datetime import datetime, timedelta
from constants import JWT_SECRET, JWT_ALGORITHM, JWT_EXP_HOURS
import helpers

def create_jwt_token(user_id: str, email: str) -> str:
    """Create a JWT token for a user."""
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXP_HOURS)
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiration
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def decode_jwt_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

def register_user(data: dict) -> dict:
    """
    Register a new user (student or tutor).
    
    Args:
        data: Dictionary with registration fields (already validated by Pydantic)
        
    Returns:
        Dictionary with success response
        
    Raises:
        ValueError
    """
    # Check if email already exists
    if helpers.email_exists(data["email"]):
        raise ValueError("email already registered")
    
    # Check if mobile already exists
    if helpers.mobile_exists(data["mobile"]):
        raise ValueError("mobile number already registered")
    
    # Generate new user ID
    user_id = helpers.get_next_user_id()
    
    # Create user dictionary with role-specific fields
    user = {
        "id": user_id,
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "email": data["email"],
        "mobile": data["mobile"],
        "password": data["password"],  # TODO: Hash this password!
        "role": "tutor" if data["tutor"] else "student",
        "payment_schedule": {},
        "availability": [],
        "enrolled_lessons": []
    }
    
    # Add role-specific fields
    if data["tutor"]:
        # Tutor-specific fields
        user.update({
            "about_me": "",
            "bank_details": {},
            "tutor_rates": {},
            "lesson_preferences": {},
            "student_ids": []
        })
    else:
        # Student-specific fields
        user.update({
            "tutor_id": None  # Will be set when assigned to a tutor
        })
    
    # Add user to database
    helpers.add_user(user)
    
    # Generate JWT token
    token = create_jwt_token(user_id, data["email"])
    
    # Return response data
    return {
        "id": user_id,
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "email": data["email"],
        "mobile": data["mobile"],
        "token": token,
        "message": "User registered successfully"
    }