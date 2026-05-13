from datetime import datetime, timedelta, timezone
import os

import jwt
from constants import JWT_ALGORITHM, JWT_SECRET
import pytest
import dataStore as ds
from server import app
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


class TestUserLogout:
    def test_logout_success(self, reset_data):
        register = client.post(
            "/users/register", 
            json={
                "first_name":"John",
                "last_name":"Doe",
                "email":"john@example.com",
                "password":"Password123_",
                "mobile":"0412345678",
                "tutor":False
            })
        data = register.json()
        token = data["token"]

        res = client.post(
            "/users/logout", 
            headers={"Authorization": f"Bearer {token}"}
        )

        assert res.json().get("message") is not None
        assert isinstance(res.json()["message"], str)
        assert res.status_code == 200

        res = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401

    def test_get_users_no_token(self, reset_data):
        res = client.post("/users/logout", headers={"Authorization": f"Bearer"})
        assert res.status_code == 401

    def test_get_users_invalid_token(self, reset_data):
        res = client.post("/users/logout", headers={"Authorization": f"Bearer invalid-token"})
        assert res.status_code == 401
    
    def test_logout_twice_same_token(self, reset_data):
        """Cannot logout twice with the same token"""
        
        register_res = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": False
            }
        )
        assert register_res.status_code == 201 

        user = register_res.json()
        token = user["token"]

        response1 = client.post(
            "/users/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response1.status_code == 200

        response2 = client.post(
            "/users/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response2.status_code == 401

    def test_logout_with_empty_bearer_token(self, reset_data):
        """Logout with malformed authorization header"""
        res = client.post("/users/logout", headers={"Authorization": "Bearer "})
        assert res.status_code == 401

    def test_logout_without_authorization_header(self, reset_data):
        """Cannot logout without Authorization header"""
        res = client.post("/users/logout")
        assert res.status_code == 401

    def test_logout_with_expired_token(self, reset_data):
        """Cannot logout with already expired token"""
        expired_payload = {
            "user_id": "999",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        res = client.post(
            "/users/logout",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert res.status_code == 401