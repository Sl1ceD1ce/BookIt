import os
import pytest
import datastore as ds
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

class TestUserLogin:
    def test_login_success(self, reset_data):
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
        res = client.post("/users/login", json={
                "email":"john@example.com",
                "password":"Password123_",
            })
        assert res.status_code == 200
        assert res.json().get("token") is not None
        assert isinstance(res.json()["token"], str)

        # checking token is actually usable with getUserInfo
        res = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json() == {
            "email":"john@example.com",
            "mobile":"0412345678",
            "first_name":"John",
            "last_name":"Doe",
            "tutor":False
        }

    def test_login_incorrect_password(self, reset_data):
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
        res = client.post("/users/login", json={
                "email":"john@example.com",
                "password":"Password123",
            })
        assert res.status_code == 400

    def test_login_incorrect_email(self, reset_data):
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
        res = client.post("/users/login", json={
                "email":"jimmy@example.com",
                "password":"Password123_",
            })
        assert res.status_code == 400