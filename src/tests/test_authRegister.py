import pytest
import dataStore as ds
import os
from server import app
from schemas import UserRegister
import auth
import helpers
from pydantic import ValidationError
import jwt
from datetime import datetime, timedelta, timezone
from constants import JWT_SECRET, JWT_ALGORITHM
from fastapi.testclient import TestClient


client = TestClient(app)

TEST_DB = "data.json"


@pytest.fixture
def reset_data():
    """Reset datastore before each test"""
    ds.data = {"users": [], "lessons": [], "invalidated_tokens": []}
    yield
    # Cleanup
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


class TestUserRegistration:

    def test_successful_register_student(self, reset_data):
        response = client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "Password123_",
            "mobile": "0412345678",
            "tutor": False,
        })
        result = response.json()
        assert response.status_code == 201
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["email"] == "john@example.com"
        assert result["mobile"] == "0412345678"
        assert "token" in result
        assert "id" in result
        assert result["message"] == "User registered successfully"
        stored_user = ds.get_data()["users"][0]
        assert stored_user["role"] == "student"
        assert stored_user.get("tutor_id") is None

    def test_successful_register_tutor(self, reset_data):
        response = client.post("/users/register", json={
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "password": "TutorPass_123",
            "mobile": "0487654321",
            "tutor": True,
        })
        result = response.json()
        assert response.status_code == 201
        stored_user = ds.get_data()["users"][0]
        assert stored_user["role"] == "tutor"
        assert all(k in stored_user for k in ("student_ids", "tutor_rates", "about_me"))

    def test_email_already_exists(self, reset_data):
        client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "Password123_",
            "mobile": "0412345678",
            "tutor": False,
        })
        response = client.post("/users/register", json={
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "john@example.com",
            "password": "DiffPassword_456",
            "mobile": "0487654321",
            "tutor": False,
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "email already registered"

    def test_mobile_already_exists(self, reset_data):
        client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "Password123_",
            "mobile": "0412345678",
            "tutor": False,
        })
        response = client.post("/users/register", json={
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "password": "DiffPassword_456",
            "mobile": "0412345678",
            "tutor": False,
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "mobile number already registered"

    @pytest.mark.parametrize("email", ["invalid-email", "wrong@.com", "noatsign.com"])
    def test_invalid_email_format(self, reset_data, email):
        response = client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": email,
            "password": "Password123_",
            "mobile": "0412345678",
            "tutor": False,
        })
        assert response.status_code == 422
        error = response.json()["detail"][0]
        assert error["loc"] == ["body", "email"]

    @pytest.mark.parametrize("password", ["Pass@word!", "Invalid$", "123#abc"])
    def test_invalid_password_format(self, reset_data, password):
        response = client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": password,
            "mobile": "0412345678",
            "tutor": False,
        })
        assert response.status_code == 422
        error = response.json()["detail"][0]
        assert error["loc"] == ["body", "password"]
        assert "letters, numbers, and underscores" in error["msg"]

    @pytest.mark.parametrize("mobile", ["1234567890", "041234567", "04123456789", "04A2345678"])
    def test_invalid_mobile_format(self, reset_data, mobile):
        response = client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "Password123_",
            "mobile": mobile,
            "tutor": False,
        })
        assert response.status_code == 422
        error = response.json()["detail"][0]
        assert error["loc"] == ["body", "mobile"]

    def test_name_too_long(self, reset_data):
        response = client.post("/users/register", json={
            "first_name": "A" * 31,
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "Password123_",
            "mobile": "0412345678",
            "tutor": False,
        })
        assert response.status_code == 422
        error = response.json()["detail"][0]
        assert error["loc"] == ["body", "first_name"]
        assert error["type"] == "string_too_long"

    @pytest.mark.parametrize("name", ["  ", ""])
    def test_empty_name_validation(self, reset_data, name):
        with pytest.raises(ValidationError):
            UserRegister(
                first_name=name,
                last_name="Doe",
                email="john@example.com",
                password="Password123_",
                mobile="0412345678",
                tutor=False,
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


class TestJWTHandling:

    def test_jwt_token_created(self, reset_data):
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
        decoded = helpers.decode_jwt_token(token)
        assert decoded["email"] == "john@example.com"
        assert "user_id" in decoded
        assert "exp" in decoded

    def test_auto_incremented_user_ids(self, reset_data):
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

    def test_expired_token_raises_error(self, reset_data):
        expired_payload = {
            "user_id": "999",
            "email": "expired@example.com",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        with pytest.raises(ValueError, match="Token has expired"):
            helpers.decode_jwt_token(token)

    def test_invalid_token_raises_error(self, reset_data):
        with pytest.raises(ValueError, match="Invalid token"):
            helpers.decode_jwt_token("invalid.token.here")

    def test_tampered_token_raises_error(self, reset_data):
        user = UserRegister(
            first_name="Tamper",
            last_name="Test",
            email="tamper@example.com",
            password="Password123_",
            mobile="0477777777",
            tutor=False
        )
        result = auth.register_user(user)
        tampered_token = result["token"] + "tamper"
        with pytest.raises(ValueError, match="Invalid token"):
            helpers.decode_jwt_token(tampered_token)
