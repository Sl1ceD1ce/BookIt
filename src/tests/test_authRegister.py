import sys
import os

#TODO: FIX THIS only a temporary fix to keep tests running so files can be accessed
# create a pyproject.toml file and a setup.py file

# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))

# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(current)

# adding the parent directory to
# the sys.path.
sys.path.append(parent)


import requests
import pytest
import dataStore as ds
import os
from server import app
from schemas import UserRegister
import auth
from pydantic import ValidationError
import jwt
from datetime import datetime, timedelta, timezone
from auth import JWT_SECRET, JWT_ALGORITHM

# Use test database
TEST_DB = "test_data.json"


@pytest.fixture
def reset_data():
    """Reset datastore before each test"""
    ds.data = {"users": [], "lessons": []}
    yield
    # Cleanup
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


@pytest.fixture
def client():
    """Create test client for FastAPI"""
    return app


class TestUserRegistration:
    def test_successful_register_student(self, reset_data):
        """Test successful student registration"""
        user_data = UserRegister(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="Password123_",
            mobile="0412345678",
            tutor=False,
        )

        result = auth.register_user(user_data)

        # Verify response structure
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["email"] == "john@example.com"
        assert result["mobile"] == "0412345678"
        assert "token" in result
        assert "id" in result
        assert result["message"] == "User registered successfully"

        # Verify user stored correctly
        stored_user = ds.get_data()["users"][0]
        assert stored_user["role"] == "student"
        assert stored_user["tutor_id"] is None

    def test_successful_register_tutor(self, reset_data):
        """Test successful tutor registration"""
        user_data = UserRegister(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            password="TutorPass_123",
            mobile="0487654321",
            tutor=True,
        )

        result = auth.register_user(user_data)

        assert result["first_name"] == "Jane"
        stored_user = ds.get_data()["users"][0]
        assert stored_user["role"] == "tutor"
        assert "student_ids" in stored_user
        assert "tutor_rates" in stored_user
        assert "about_me" in stored_user

    def test_email_already_exists(self, reset_data):
        """Test registration fails when email already exists"""
        user_data = UserRegister(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="Password123_",
            mobile="0412345678",
            tutor=False,
        )

        # Register first user
        auth.register_user(user_data)

        # Try to register with same email
        duplicate_user = UserRegister(
            first_name="Jane",
            last_name="Smith",
            email="john@example.com",  # Same email
            password="DiffPassword_456",
            mobile="0487654321",
            tutor=False,
        )

        with pytest.raises(ValueError, match="email already registered"):
            auth.register_user(duplicate_user)

    def test_mobile_already_exists(self, reset_data):
        """Test registration fails when mobile number already exists"""
        user_data = UserRegister(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="Password123_",
            mobile="0412345678",
            tutor=False,
        )

        auth.register_user(user_data)

        duplicate_mobile = UserRegister(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            password="DiffPassword_456",
            mobile="0412345678",  # Same mobile
            tutor=False,
        )

        with pytest.raises(ValueError, match="mobile number already registered"):
            auth.register_user(duplicate_mobile)

    def test_invalid_email_format(self, reset_data):
        """Test validation catches invalid email"""
        with pytest.raises(ValueError):
            UserRegister(
                first_name="John",
                last_name="Doe",
                email="invalid-email",
                password="Password123_",
                mobile="0412345678",
                tutor=False,
            )

    def test_invalid_password_format(self, reset_data):
        """Test validation catches invalid password characters"""
        with pytest.raises(ValueError, match="password can only contain"):
            UserRegister(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                password="Pass@word!",  # Special chars not allowed
                mobile="0412345678",
                tutor=False,
            )

    def test_invalid_mobile_format(self, reset_data):
        """Test validation catches invalid mobile number"""
        with pytest.raises(ValueError, match="invalid mobile number format"):
            UserRegister(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                password="Password123_",
                mobile="1234567890",  # Doesn't start with 04
                tutor=False,
            )

    def test_empty_name_validation(self, reset_data):
        """Test validation rejects empty or whitespace names"""
        with pytest.raises(ValueError, match="name cannot be empty"):
            UserRegister(
                first_name="   ",
                last_name="Doe",
                email="john@example.com",
                password="Password123_",
                mobile="0412345678",
                tutor=False,
            )

    def test_name_too_long(self, reset_data):
        """Test validation rejects names exceeding max length"""
        with pytest.raises(ValueError):
            UserRegister(
                first_name="A" * 31,  # Exceeds max of 30
                last_name="Doe",
                email="john@example.com",
                password="Password123_",
                mobile="0412345678",
                tutor=False,
            )

    def test_jwt_token_created(self, reset_data):
        """Test JWT token is properly created and contains user info"""
        user_data = UserRegister(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="Password123_",
            mobile="0412345678",
            tutor=False,
        )

        result = auth.register_user(user_data)
        token = result["token"]

        # Decode token to verify payload
        decoded = auth.decode_jwt_token(token)
        assert decoded["email"] == "john@example.com"
        assert "user_id" in decoded
        assert "exp" in decoded

    def test_auto_incremented_user_ids(self, reset_data):
        """Test user IDs are auto-incremented correctly"""
        user1 = UserRegister(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="Password123_",
            mobile="0412345678",
            tutor=False,
        )

        user2 = UserRegister(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            password="Password456_",
            mobile="0487654321",
            tutor=False,
        )

        result1 = auth.register_user(user1)
        result2 = auth.register_user(user2)

        assert result1["id"] == "1"
        assert result2["id"] == "2"
    
    def test_password_too_long(self, reset_data):
        """Test validation rejects password exceeding length requirement"""
        with pytest.raises(ValidationError):
            UserRegister(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                password="A" * 31,
                mobile="0412345678",
                tutor=False,
            )
    
    def test_password_too_short(self, reset_data):
        """Test validation rejects password below length requirement"""
        with pytest.raises(ValidationError):
            UserRegister(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                password="",
                mobile="0412345678",
                tutor=False,
            )

    def test_email_max_length(self, reset_data):
        """Test email at max allowed length (50 chars) is accepted"""
        local_part = "a" * 38  # "a" * 38 + "@e.com" = 50
        email = f"{local_part}@e.com"
        user = UserRegister(
            first_name="Max",
            last_name="Email",
            email=email,
            password="Password123_",
            mobile="0412345678",
            tutor=False
        )
        assert user.email == email

    def test_email_exceeds_max_length(self, reset_data):
        """Test email exceeding 50 chars is rejected"""
        local_part = "a" * 50  # 39 + "@e.com" = 51
        email = f"{local_part}@gmail.com"
        with pytest.raises(ValidationError):
            UserRegister(
                first_name="Too",
                last_name="LongEmail",
                email=email,
                password="Password123_",
                mobile="0412345678",
                tutor=False
            )

    @pytest.mark.parametrize("mobile_input", [
        "041234567",    # too short
        "04123456789",  # too long
        "04A2345678",   # contains letter
    ])
    def test_invalid_mobile_edge_cases(self, reset_data, mobile_input):
        with pytest.raises(ValueError, match="invalid mobile number format"):
            UserRegister(
                first_name="Dave",
                last_name="Edge",
                email="dave@example.com",
                password="Password123_",
                mobile=mobile_input,
                tutor=False
            )

    @pytest.mark.parametrize("mobile_input, expected", [
        ("0412 345 678", "0412345678"),
        ("0412-345-678", "0412345678"),
    ])
    def test_mobile_with_spaces_or_dashes(self, reset_data, mobile_input, expected):
        user = UserRegister(
            first_name="Charlie",
            last_name="Dash",
            email="charlie@example.com",
            password="Password123_",
            mobile=mobile_input,
            tutor=False
        )
        assert user.mobile == expected

    def test_name_with_spaces_stripped(self, reset_data):
        user = UserRegister(
            first_name="  Alice  ",
            last_name="  Smith  ",
            email="spaces@example.com",
            password="Password123_",
            mobile="0466666666",
            tutor=False
        )
        assert user.first_name == "Alice"
        assert user.last_name == "Smith"


class TestTokenHandling:

    def test_jwt_token_expiration(self, reset_data):
        """Test JWT token includes expiration"""
        token = auth.create_jwt_token("1", "test@example.com")
        decoded = auth.decode_jwt_token(token)

        assert "exp" in decoded

    def test_invalid_token_raises_error(self, reset_data):
        """Test decoding invalid token raises error"""
        with pytest.raises(ValueError, match="Invalid token"):
            auth.decode_jwt_token("invalid.token.here")

    def test_decode_includes_user_data(self, reset_data):
        """Test decoded token includes user_id and email"""
        token = auth.create_jwt_token("123", "user@example.com")
        decoded = auth.decode_jwt_token(token)

        assert decoded["user_id"] == "123"
        assert decoded["email"] == "user@example.com"
    
    def test_expired_token_raises_error(self, reset_data):
        """Test decoding an expired JWT raises error"""
        expired_payload = {
            "user_id": "999",
            "email": "expired@example.com",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        with pytest.raises(ValueError, match="Token has expired"):
            auth.decode_jwt_token(token)
        
    def test_tampered_token_raises_error(self, reset_data):
        """Test decoding a tampered JWT raises error"""
        user = UserRegister(
            first_name="Tamper",
            last_name="Test",
            email="tamper@example.com",
            password="Password123_",
            mobile="0477777777",
            tutor=False
        )
        result = auth.register_user(user)
        token = result["token"]
        tampered_token = token + "tamper"
        with pytest.raises(ValueError, match="Invalid token"):
            auth.decode_jwt_token(tampered_token)
