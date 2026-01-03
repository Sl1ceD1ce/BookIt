import sys
import os
import pytest
import dataStore as ds
from server import app
from fastapi.testclient import TestClient

client = TestClient(app)

TEST_DB = "data.json"

@pytest.fixture
def reset_data():
    """Reset datastore before each test"""
    ds.data = {"users": [], "lessons": []}
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
        
        