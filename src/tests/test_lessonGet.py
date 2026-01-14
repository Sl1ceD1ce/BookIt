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

    def test_get_student_lessons_after_booking(self, reset_data):
        # Register tutor
        tutor_token = client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "Password123_",
            "mobile": "0412345678",
            "tutor": True,
        }).json()["token"]

        # Register student
        student_token = client.post("/users/register", json={
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "password": "Password123_",
            "mobile": "0498765432",
            "tutor": False,
        }).json()["token"]

        # Tutor creates a lesson
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=60)
        lesson = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Physics"
            }
        ).json()

        # Student books the lesson
        client.post(
            f"/lessons/{lesson['lesson_id']}/book",
            headers={"Authorization": f"Bearer {student_token}"}
        )

        # Student fetches their lessons
        get_res = client.get(
            "/lessons",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert get_res.status_code == 200
        lessons_list = get_res.json()

        assert len(lessons_list) == 1
        booked_lesson = lessons_list[0]
        assert booked_lesson["lesson_id"] == lesson["lesson_id"]
        assert booked_lesson["subject"] == "Physics"
        assert booked_lesson["tutor_email"] == "john@example.com"
        assert booked_lesson["student_email"] == "alice@example.com"
        assert booked_lesson["status"] == "Booked"

    def test_get_lessons_multiple_users(self, reset_data):
        # Register tutor
        tutor1_token = client.post("/users/register", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "Password123_",
            "mobile": "0412345678",
            "tutor": True,
        }).json()["token"]

        tutor2_token = client.post("/users/register", json={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "password": "Password123_",
            "mobile": "0412345679",
            "tutor": True,
        }).json()["token"]

        # Register students
        student1_token = client.post("/users/register", json={
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "password": "Password123_",
            "mobile": "0498765432",
            "tutor": False,
        }).json()["token"]

        student2_token = client.post("/users/register", json={
            "first_name": "Bob",
            "last_name": "Smith",
            "email": "bob@example.com",
            "password": "Password123_",
            "mobile": "0498765433",
            "tutor": False,
        }).json()["token"]

        # Tutor1 creates a lesson
        lesson1 = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {tutor1_token}"},
            json={
                "start_time": datetime.now().isoformat(),
                "end_time": (datetime.now() + timedelta(hours=1)).isoformat(),
                "subject": "Physics"
            }
        ).json()

        # Tutor2 creates a lesson
        lesson2 = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {tutor2_token}"},
            json={
                "start_time": datetime.now().isoformat(),
                "end_time": (datetime.now() + timedelta(hours=1)).isoformat(),
                "subject": "Chemistry"
            }
        ).json()

        # Student1 books lesson1
        client.post(
            f"/lessons/{lesson1['lesson_id']}/book",
            headers={"Authorization": f"Bearer {student1_token}"}
        )

        # Student2 books lesson2
        client.post(
            f"/lessons/{lesson2['lesson_id']}/book",
            headers={"Authorization": f"Bearer {student2_token}"}
        )

        # Each student fetches their lessons
        res1 = client.get("/lessons", headers={"Authorization": f"Bearer {student1_token}"})
        res2 = client.get("/lessons", headers={"Authorization": f"Bearer {student2_token}"})

        lessons1 = res1.json()
        lessons2 = res2.json()

        assert len(lessons1) == 1
        assert lessons1[0]["lesson_id"] == lesson1["lesson_id"]
        assert lessons1[0]["student_email"] == "alice@example.com"

        assert len(lessons2) == 1
        assert lessons2[0]["lesson_id"] == lesson2["lesson_id"]
        assert lessons2[0]["student_email"] == "bob@example.com"