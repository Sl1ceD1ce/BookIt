import sys
import os
import requests
import pytest
import dataStore as ds
from server import app
import auth
from schemas import UserRegister

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

class TestUserInfo:
    def test_get_users_success_student(self, reset_data):
        user_data = UserRegister(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="Password123_",
            mobile="0412345678",
            tutor=False,
        )
        registered_user = auth.register_user(user_data)

        token = registered_user["token"]
        res = auth.get_users(token)
        assert res["email"] == "john@example.com"
        assert res["mobile"] == "0412345678"
        assert res["first_name"] == "John"
        assert res["last_name"] == "Doe"
        assert res["tutor"] == False
    
    def test_get_users_success_tutor(self, reset_data):
        user_data = UserRegister(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="Password123_",
            mobile="0412345678",
            tutor=True,
        )
        registered_user = auth.register_user(user_data)

        token = registered_user["token"]
        res = auth.get_users(token)
        assert res["email"] == "john@example.com"
        assert res["mobile"] == "0412345678"
        assert res["first_name"] == "John"
        assert res["last_name"] == "Doe"
        assert res["tutor"] == True
    
    def test_get_users_no_token(self, reset_data):
        with pytest.raises(ValueError):
            auth.get_users("")

    def test_get_users_invalid_token(self, reset_data):
        with pytest.raises(ValueError):
            auth.get_users("invalid-token")
        
        