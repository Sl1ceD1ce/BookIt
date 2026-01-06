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

class TestLessonCreate:

    def test_successful_lesson_creation(self, reset_data):
        register = client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "Password123_",
            "mobile": "0412345678",
            "tutor": True,
        })
        data = register.json()
        user_token = data["token"]
        start_time = datetime(2026, 1, 6, 8, 0) # 2026-01-06 08:00:00
        end_time = start_time + timedelta(minutes=60)
        
        res = client.post("/lessons/", headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            })

        res_data = res.json()

        assert res.status_code == 201
        assert "lesson_id" in res_data
        assert res_data["start_time"] == start_time.isoformat()
        assert res_data["end_time"] == end_time.isoformat()
        assert res_data["duration"] == 60
        assert res_data["tutor_email"] == "john@example.com"
        assert res_data["student_email"] is None
        assert res_data["status"] == "Available"

    def test_unsuccessful_lesson_creation_student(self, reset_data):
        register = client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "Password123_",
            "mobile": "0412345678",
            "tutor": False,
        })
        data = register.json()
        user_token = data["token"]
        start_time = datetime(2026, 1, 6, 8, 0) # 2026-01-06 08:00:00
        end_time = start_time + timedelta(minutes=60)
        res = client.post("/lessons/", headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            })
        
        assert res.status_code == 403

    def test_unsuccessful_lesson_creation_too_long(self, reset_data):
        register = client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "Password123_",
            "mobile": "0412345678",
            "tutor": True,
        })
        data = register.json()
        user_token = data["token"]
        start_time = datetime(2026, 1, 6, 8, 0) # 2026-01-06 08:00:00
        end_time = start_time + timedelta(minutes=240)
        res = client.post("/lessons/", headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            })
        
        assert res.status_code == 400
    
    def test_unsuccessful_lesson_creation_invalid_duration(self, reset_data):
        register = client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "Password123_",
            "mobile": "0412345678",
            "tutor": True,
        })
        data = register.json()
        user_token = data["token"]
        start_time = datetime(2026, 1, 6, 8, 0) # 2026-01-06 08:00:00
        end_time = start_time + timedelta(minutes=-20)
        res = client.post("/lessons/", headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            })
        
        assert res.status_code == 400