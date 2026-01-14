import os
import pytest
import dataStore as ds
from server import app
from datetime import datetime, timedelta
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

class TestLessonGet:
    def test_get_tutor_lessons(self, reset_data):
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

        start_time = datetime(2026, 1, 6, 8, 0)
        end_time = start_time + timedelta(minutes=60)

        create_res = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Math"
            }
        )
        assert create_res.status_code == 201
        lesson = create_res.json()

        get_res = client.get(
            "/lessons",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert get_res.status_code == 200
        lessons = get_res.json()

        assert len(lessons) == 1
        assert lessons[0]["lesson_id"] == lesson["lesson_id"]
        assert lessons[0]["subject"] == "Math"
        assert lessons[0]["tutor_email"] == "john@example.com"
        assert lessons[0]["student_email"] is None
        assert lessons[0]["status"] == "Available"