import os
import pytest
import data_store as ds
from server import app
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

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


sampleTutor1 = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "password": "Password123_",
    "mobile": "0412345678",
    "tutor": True,
}

sampleTutor2 = {
    "first_name": "Richard",
    "last_name": "Zhang",
    "email": "richardzhang@gmail.com",
    "password": "slickPassword22_",
    "mobile": "0493107678",
    "tutor": True,
}

sampleStudent1 = {
    "first_name": "Jimmy",
    "last_name": "Butler",
    "email": "jimmybutler@example.com",
    "password": "Password435_",
    "mobile": "0412342149",
    "tutor": False,
}

sampleStudent2 = {
    "first_name": "Steph",
    "last_name": "Curry",
    "email": "stephcurry@example.com",
    "password": "Sl1ckPassword123_",
    "mobile": "0412342748",
    "tutor": False,
}

startTime = datetime.now() + timedelta(minutes=60)
endTime  = startTime + timedelta(minutes=60)
newStart = startTime + timedelta(days=1)
newEnd = newStart + timedelta(minutes=60)

class TestAuthDelete:
    def test_successfulDeleteTutor(self, reset_data):
        register = client.post("/users/register", json=sampleTutor1)

        data = register.json()
        tutor1Token = data["token"]

        register = client.post("/users/register", json=sampleTutor2)

        data = register.json()
        tutor2Token = data["token"]

        deleteRes = client.delete(
            "/users",
            headers={"Authorization": f"Bearer {tutor1Token}"},
        )

        assert deleteRes.status_code == 200

        # ensure that delete was completed
        getResTutor1 = client.get(
            "/users",
            headers={"Authorization": f"Bearer {tutor1Token}"},
        )
        assert getResTutor1.status_code == 401

        # ensure other tutor wasn't deleted
        getResTutor2 = client.get(
            "/users",
            headers={"Authorization": f"Bearer {tutor2Token}"},
        )
        assert getResTutor2.status_code == 200

    def test_successfulDeleteStudent(self, reset_data):
        register = client.post("/users/register", json=sampleStudent1)

        data = register.json()
        student1Token = data["token"]

        register = client.post("/users/register", json=sampleStudent2)

        data = register.json()
        student2Token = data["token"]

        deleteRes = client.delete(
            "/users",
            headers={"Authorization": f"Bearer {student1Token}"},
        )
        assert deleteRes.status_code == 200

        # ensure that delete was completed
        getRes = client.get(
            "/users",
            headers={"Authorization": f"Bearer {student1Token}"},
        )
        assert getRes.status_code == 401

        # ensure other student wasn't deleted
        getRes = client.get(
            "/users",
            headers={"Authorization": f"Bearer {student2Token}"},
        )
        assert getRes.status_code == 200

    def test_deleteWithInvalidToken(self, reset_data):
        deleteRes = client.delete(
            "/users",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert deleteRes.status_code == 401

    def test_deleteWithoutToken(self, reset_data):
        deleteRes = client.delete("/users")
        assert deleteRes.status_code == 401

    def test_deleteNonexistentUser(self, reset_data):
        # Create a user and get token
        register = client.post("/users/register", json=sampleTutor1)
        data = register.json()
        userToken = data["token"]

        # Delete the user
        deleteRes = client.delete(
            "/users",
            headers={"Authorization": f"Bearer {userToken}"},
        )
        assert deleteRes.status_code == 200

        # Try to delete again with same token
        deleteRes2 = client.delete(
            "/users",
            headers={"Authorization": f"Bearer {userToken}"},
        )
        assert deleteRes2.status_code == 401
