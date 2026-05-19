import pytest
from schemas import UserRegister
import auth
import helpers
from pydantic import ValidationError
import jwt
from datetime import datetime, timedelta, timezone
from constants import JWT_SECRET, JWT_ALGORITHM


class TestUserRegistration:

    def test_successful_register_student(self, client):
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

    def test_successful_register_tutor(self, client):
        response = client.post("/users/register", json={
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "password": "TutorPass_123",
            "mobile": "0487654321",
            "tutor": True,
        })
        assert response.status_code == 201

    def test_email_already_exists(self, client):
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

    def test_mobile_already_exists(self, client):
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
    def test_invalid_email_format(self, client, email):
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

    @pytest.mark.parametrize("password", ["Pass@word!", "sl1ckPassw1rd", "pass"])
    def test_invalid_password_formats(self, client, password):
        response = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": password,
                "mobile": "0412345678",
                "tutor": False,
            },
        )

    @pytest.mark.parametrize("password", ["Pass@word!", "Invalid$", "123#abc"])
    def test_invalid_password_format(self, client, password):
        response = client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": password,
            "mobile": "0412345678",
            "tutor": False,
        })
        assert response.status_code == 422

    @pytest.mark.parametrize("mobile", ["1234567890", "041234567", "04123456789", "04A2345678"])
    def test_invalid_mobile_format(self, client, mobile):
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

    def test_name_too_long(self, client):
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
    def test_empty_name_validation(self, name):
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
    def test_mobile_with_spaces_or_dashes(self, mobile_input, expected):
        user = UserRegister(
            first_name="Charlie",
            last_name="Dash",
            email="charlie@example.com",
            password="Password123_",
            mobile=mobile_input,
            tutor=False
        )
        assert user.mobile == expected

    def test_name_with_spaces_stripped(self):
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

    def test_jwt_token_created(self, db):
        user_data = UserRegister(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="Password123_",
            mobile="0412345678",
            tutor=False,
        )
        result = auth.register_user(user_data, db)
        token = result["token"]
        decoded = helpers.decode_jwt_token(token)
        assert "user_id" in decoded
        assert "exp" in decoded

    def test_non_empty_user_ids(self, db):
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
        result1 = auth.register_user(user1, db)
        result2 = auth.register_user(user2, db)

        assert result1["id"] is not None
        assert result2["id"] is not None
        assert isinstance(result1["id"], str)
        assert isinstance(result2["id"], str)
        assert result1["id"].strip() != ""
        assert result2["id"].strip() != ""

    def test_tampered_token_raises_error(self, db):
        user = UserRegister(
            first_name="Tamper",
            last_name="Test",
            email="tamper@example.com",
            password="Password123_",
            mobile="0477777777",
            tutor=False
        )
        result = auth.register_user(user, db)
        tampered_token = result["token"] + "tamper"
        with pytest.raises(ValueError, match="Invalid token"):
            helpers.decode_jwt_token(tampered_token)

    def test_expired_token_raises_error(self):
        expired_payload = {
            "user_id": "999",
            "email": "expired@example.com",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        with pytest.raises(ValueError, match="Token has expired"):
            helpers.decode_jwt_token(token)

    def test_invalid_token_raises_error(self):
        with pytest.raises(ValueError, match="Invalid token"):
            helpers.decode_jwt_token("invalid.token.here")