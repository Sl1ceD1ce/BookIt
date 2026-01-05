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
        

        