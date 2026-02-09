import os
import pytest
import dataStore as ds
from server import app
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from helpers import decode_jwt_token

client = TestClient(app)

TEST_DB = "data.json"

default_start = datetime.now() + timedelta(minutes=60)
default_end = default_start + timedelta(minutes=60)
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
        register = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        )
        data = register.json()
        user_token = data["token"]
        start_time = default_start  # 2026-01-06 08:00:00
        end_time = default_end
        res = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Math",
            },
        )

        res_data = res.json()

        assert res.status_code == 201
        assert "lesson_id" in res_data
        assert res_data["start_time"] == start_time.isoformat()
        assert res_data["end_time"] == end_time.isoformat()
        assert res_data["duration"] == 60
        assert res_data["subject"] == "Math"
        assert res_data["tutor_id"] == decode_jwt_token(user_token)["user_id"]
        assert res_data["assigned_student_id"] is None
        assert res_data["available"] == True

    def test_invalid_token(self, reset_data):
        start_time = default_start  # 2026-01-06 08:00:00
        end_time = default_end

        res = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {'sdfsdfg'}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Math",
            },
        )

        assert res.status_code == 401
        

    def test_unsuccessful_lesson_creation_student(self, reset_data):
        register = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": False,
            },
        )
        data = register.json()
        user_token = data["token"]
        start_time = default_start  # 2026-01-06 08:00:00
        end_time = default_end
        res = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "English",
            },
        )

        assert res.status_code == 403

    def test_unsuccessful_lesson_creation_invalid_duration(self, reset_data):
        register = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        )
        data = register.json()
        user_token = data["token"]
        start_time = default_start  # 2026-01-06 08:00:00
        end_time = start_time + timedelta(minutes=-20)
        res = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "History",
            },
        )

        assert res.status_code == 400

    def test_unsuccessful_lesson_creation_overlap(self, reset_data):
        register = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        )
        data = register.json()
        user_token = data["token"]

        start_time_1 = default_start
        end_time_1 = default_end
        res1 = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time_1.isoformat(),
                "end_time": end_time_1.isoformat(),
                "subject": "Math",
            },
        )
        assert res1.status_code == 201

        start_time_2 = default_start + timedelta(minutes=30)
        end_time_2 = start_time_2 + timedelta(minutes=60)
        res2 = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time_2.isoformat(),
                "end_time": end_time_2.isoformat(),
                "subject": "History",
            },
        )

        assert res2.status_code == 400 or res2.status_code == 409
        assert "overlaps" in res2.json()["detail"].lower()

    def test_invalid_time_values(self, reset_data):
        register = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        )
        data = register.json()
        user_token = data["token"]
        start_time = "2026-14-06T09:00:00"
        end_time = datetime(2026, 1, 6, 9, 0)

        res = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time,
                "end_time": end_time.isoformat(),
                "subject": "Math",
            },
        )

        assert res.status_code == 401
    
    def test_invalid_time_format(self, reset_data):
        register = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        )
        data = register.json()
        user_token = data["token"]
        start_time = "2026-03"
        end_time = datetime(2026, 1, 6, 9, 0)

        res = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time,
                "end_time": end_time.isoformat(),
                "subject": "Math",
            },
        )
        assert res.status_code == 401

    def test_invalid_time_empty(self, reset_data):
        register = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        )
        data = register.json()
        user_token = data["token"]
        start_time = ""
        end_time = datetime(2026, 1, 6, 9, 0)

        res = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time,
                "end_time": end_time.isoformat(),
                "subject": "Math",
            },
        )
        assert res.status_code == 401

    def test_successful_lesson_creation_boundary(self, reset_data):
        register = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        )
        data = register.json()
        user_token = data["token"]

        start_time_1 = default_start
        end_time_1 = default_end
        res1 = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time_1.isoformat(),
                "end_time": end_time_1.isoformat(),
                "subject": "Math",
            },
        )
        assert res1.status_code == 201

        start_time_2 = default_start + timedelta(minutes=60)
        end_time_2 = start_time_2 + timedelta(minutes=60)
        res2 = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time_2.isoformat(),
                "end_time": end_time_2.isoformat(),
                "subject": "History",
            },
        )

        assert res2.status_code == 201

    def test_same_time_different_tutor(self, reset_data):
        register1 = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        )
        data1 = register1.json()
        user_token1 = data1["token"]

        register2 = client.post(
            "/users/register",
            json={
                "first_name": "Sherman",
                "last_name": "Doe",
                "email": "hello@example.com",
                "password": "Password12_",
                "mobile": "0412345697",
                "tutor": True,
            },
        )
        data2 = register2.json()
        user_token2 = data2["token"]

        start_time = default_start
        end_time = default_end

        res1 = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {user_token1}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Math",
            },
        )

        assert res1.status_code == 201

        res2 = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {user_token2}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Math",
            },
        )

        assert res2.status_code == 201
    
    def test_unsuccessful_lesson_creation_past(self, reset_data):
        register = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        )
        data = register.json()
        user_token = data["token"]
        start_time = datetime.now() - timedelta(minutes=30)  # 2026-01-06 08:00:00
        end_time = start_time + timedelta(minutes=60)
        res = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Math",
            },
        )
        assert res.status_code == 400
        