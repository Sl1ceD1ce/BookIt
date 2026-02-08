import os
import pytest
import dataStore as ds
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


sampleTutor = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "password": "Password123_",
    "mobile": "0412345678",
    "tutor": True,
}

sampleStudent = {
    "first_name": "Jimmy",
    "last_name": "Butler",
    "email": "jimmybutler@example.com",
    "password": "Password435_",
    "mobile": "0412342149",
    "tutor": False,
}

startTime = datetime(2026, 1, 6, 8, 0)  # 2026-01-06 08:00:00
endTime = startTime + timedelta(minutes=60)
newStart = datetime(2026, 1, 7, 8, 0)  # 2026-01-06 08:00:00
newEnd = newStart + timedelta(minutes=60)

sampleLesson = {
    "start_time": startTime.isoformat(),
    "end_time": endTime.isoformat(),
    "subject": "Math",
}

class TestAuthDelete:
    def test_successfulDelete(self, reset_data):
        register = client.post("/users/register", json=sampleTutor)
    
        data = register.json()
        userToken = data["token"]

        deleteRes = client.delete(
            "/users",  
            headers={"Authorization": f"Bearer {userToken}"},)
        
        deleteRes.status_code == 200

    # def test_successfulDeleteV2(self, reset_data):
    # def test_successfulDeleteFromGroup(self, reset_data):
    # def test_expiredToken(self, reset_data):
    # def test_invalidToken(self, reset_data):