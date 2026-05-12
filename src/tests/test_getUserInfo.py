from datetime import datetime, timedelta, timezone
import os

import jwt
from constants import JWT_ALGORITHM, JWT_SECRET
import pytest
import data_store as ds
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

class TestUserInfo:
    def test_get_users_success_student(self, reset_data):
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
        res = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json() == {
            "email":"john@example.com",
            "mobile":"0412345678",
            "first_name":"John",
            "last_name":"Doe",
            "tutor":False
        }
    
    def test_get_users_success_tutor(self, reset_data):
        register = client.post(
            "/users/register", 
            json={
                "first_name":"John",
                "last_name":"Doe",
                "email":"john@example.com",
                "password":"Password123_",
                "mobile":"0412345678",
                "tutor":True
            })
        data = register.json()
        token = data["token"]
        res = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json() == {
            "email":"john@example.com",
            "mobile":"0412345678",
            "first_name":"John",
            "last_name":"Doe",
            "tutor":True
        }
    
    def test_get_users_no_token(self, reset_data):
        res = client.get("/users/", headers={"Authorization": f"Bearer"})
        assert res.status_code == 401

    def test_get_users_invalid_token(self, reset_data):
        res = client.get("/users/", headers={"Authorization": f"Bearer invalid-token"})
        assert res.status_code == 401
    
    def test_get_users_without_authorization_header(self, reset_data):
        """Cannot get user info without Authorization header"""
        res = client.get("/users/")
        assert res.status_code == 401
    
    def test_get_users_after_logout(self, reset_data):
        """Cannot get user info after logging out"""
        register = client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "Password123_",
            "mobile": "0412345678",
            "tutor": False
        })
        token = register.json()["token"]
        
        # Logout
        client.post("/users/logout", headers={"Authorization": f"Bearer {token}"})
        
        # Try to get user info
        res = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401
    
    def test_get_users_with_expired_token(self, reset_data):
        """Cannot get user info with expired token"""
        expired_payload = {
            "user_id": "999",
            "email": "expired@example.com",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        res = client.get("/users/", headers={"Authorization": f"Bearer {expired_token}"})
        assert res.status_code == 401
    
    def test_multiple_get_users(self, reset_data):
        """Get user info returns the correct user's data"""
        # Register two users
        user1 = client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "Password123_",
            "mobile": "0412345678",
            "tutor": False
        })
        
        user2 = client.post("/users/register", json={
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "password": "Password456_",
            "mobile": "0487654321",
            "tutor": False
        })
        
        token1 = user1.json()["token"]
        token2 = user2.json()["token"]
        
        # Get user1's info
        res1 = client.get("/users/", headers={"Authorization": f"Bearer {token1}"})
        assert res1.json()["email"] == "john@example.com"
        
        # Get user2's info
        res2 = client.get("/users/", headers={"Authorization": f"Bearer {token2}"})
        assert res2.json()["email"] == "jane@example.com"
