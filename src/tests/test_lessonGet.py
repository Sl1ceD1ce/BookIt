import os
import pytest
import data_store as ds
from server import app
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from helpers import decode_jwt_token


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

default_start = datetime.now() + timedelta(minutes=60)
default_end = default_start + timedelta(minutes=60)

class TestLessonGet:
    def test_get_tutor_lessons(self, reset_data):
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

        start_time = default_start
        end_time = start_time + timedelta(minutes=60)

        create_res = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Math",
            },
        )
        assert create_res.status_code == 201
        lesson = create_res.json()

        get_res = client.get(
            "/lessons", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert get_res.status_code == 200
        lessons = get_res.json()

        assert len(lessons) == 1
        assert lessons[0]["lesson_id"] == lesson["lesson_id"]
        assert lessons[0]["subject"] == "Math"
        assert lessons[0]["tutor_id"] == decode_jwt_token(user_token)["user_id"]
        assert lessons[0]["assigned_student_id"] is None
        assert lessons[0]["available"] == True

    def test_get_student_lessons_after_booking(self, reset_data):
        # Register tutor
        tutor_token = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        ).json()["token"]

        # Register student
        student_token = client.post(
            "/users/register",
            json={
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "alice@example.com",
                "password": "Password123_",
                "mobile": "0498765432",
                "tutor": False,
            },
        ).json()["token"]

        # Tutor creates a lesson
        start_time = default_start
        end_time = start_time + timedelta(minutes=60)
        lesson = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Physics",
            },
        ).json()

        # Student books the lesson
        client.post(
            f"/lessons/{lesson['lesson_id']}/book",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Student fetches their lessons
        get_res = client.get(
            "/lessons", headers={"Authorization": f"Bearer {student_token}"}
        )
        assert get_res.status_code == 200
        lessons_list = get_res.json()

        assert len(lessons_list) == 1
        booked_lesson = lessons_list[0]
        assert booked_lesson["lesson_id"] == lesson["lesson_id"]
        assert booked_lesson["subject"] == "Physics"
        assert booked_lesson["tutor_id"] == decode_jwt_token(tutor_token)["user_id"]
        assert booked_lesson["assigned_student_id"] == decode_jwt_token(student_token)["user_id"]
        assert booked_lesson["available"] == False

    def test_get_lessons_multiple_users(self, reset_data):
        # Register tutor
        tutor1_token = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        ).json()["token"]

        tutor2_token = client.post(
            "/users/register",
            json={
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@example.com",
                "password": "Password123_",
                "mobile": "0412345679",
                "tutor": True,
            },
        ).json()["token"]

        # Register students
        student1_token = client.post(
            "/users/register",
            json={
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "alice@example.com",
                "password": "Password123_",
                "mobile": "0498765432",
                "tutor": False,
            },
        ).json()["token"]

        student2_token = client.post(
            "/users/register",
            json={
                "first_name": "Bob",
                "last_name": "Smith",
                "email": "bob@example.com",
                "password": "Password123_",
                "mobile": "0498765433",
                "tutor": False,
            },
        ).json()["token"]

        # Tutor1 creates a lesson
        lesson1 = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {tutor1_token}"},
            json={
                "start_time": default_start.isoformat(),
                "end_time": default_end.isoformat(),
                "subject": "Physics",
            },
        ).json()

        # Tutor2 creates a lesson
        lesson2 = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {tutor2_token}"},
            json={
                "start_time": default_start.isoformat(),
                "end_time": default_end.isoformat(),
                "subject": "Chemistry",
            },
        ).json()

        # Student1 books lesson1
        client.post(
            f"/lessons/{lesson1['lesson_id']}/book",
            headers={"Authorization": f"Bearer {student1_token}"},
        )

        # Student2 books lesson2
        client.post(
            f"/lessons/{lesson2['lesson_id']}/book",
            headers={"Authorization": f"Bearer {student2_token}"},
        )

        # Each student fetches their lessons
        res1 = client.get(
            "/lessons", headers={"Authorization": f"Bearer {student1_token}"}
        )
        res2 = client.get(
            "/lessons", headers={"Authorization": f"Bearer {student2_token}"}
        )

        lessons1 = res1.json()
        lessons2 = res2.json()

        assert len(lessons1) == 1
        assert lessons1[0]["lesson_id"] == lesson1["lesson_id"]
        assert lessons1[0]["assigned_student_id"] == decode_jwt_token(student1_token)["user_id"]

        assert len(lessons2) == 1
        assert lessons2[0]["lesson_id"] == lesson2["lesson_id"]
        assert lessons2[0]["assigned_student_id"] == decode_jwt_token(student2_token)["user_id"]

    def test_get_student_lessons_multiple(self, reset_data):
        # Register tutor
        tutor_token = client.post(
            "/users/register",
            json={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        ).json()["token"]

        # Register student
        student_token = client.post(
            "/users/register",
            json={
                "first_name": "Alice",
                "last_name": "Smith",
                "email": "alice@example.com",
                "password": "Password123_",
                "mobile": "0498765432",
                "tutor": False,
            },
        ).json()["token"]

        # Tutor creates a lesson
        start_time = default_start
        end_time = start_time + timedelta(minutes=60)
        lesson = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Physics",
            },
        ).json()

        lesson2 = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "start_time": (start_time + timedelta(hours=1)).isoformat(),
                "end_time": (end_time + timedelta(minutes=60)).isoformat(),
                "subject": "Math",
            },
        ).json()
        # Student books the lesson
        client.post(
            f"/lessons/{lesson['lesson_id']}/book",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        client.post(
            f"/lessons/{lesson2['lesson_id']}/book",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Student fetches their lessons
        get_res = client.get(
            "/lessons", headers={"Authorization": f"Bearer {student_token}"}
        )
        assert get_res.status_code == 200
        assert len(get_res.json()) == 2

    def test_get_tutor_lessons_none(self, reset_data):
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

        get_res = client.get(
            "/lessons", headers={"Authorization": f"Bearer {user_token}"}
        )

        assert get_res.status_code == 200
        lessons = get_res.json()

        assert len(lessons) == 0

    def test_get_invalid_token(self, reset_data):
        get_res = client.get(
            "/lessons", headers={"Authorization": "Bearer fasdfasdf"}
        )
        assert get_res.status_code == 401
    
    def test_get_logged_out(self, reset_data):
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
        client.post(
            "/users/logout", 
            headers={"Authorization": f"Bearer {user_token}"}
        )
        get_res = client.get(
            "/lessons", headers={"Authorization": f"Bearer {user_token}"}
        )
        assert get_res.status_code == 401

    def test_tutor_doesnt_see_other_lesson(self, reset_data):
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
                "first_name": "John",
                "last_name": "Doe",
                "email": "hello@example.com",
                "password": "Password12_",
                "mobile": "0412345679",
                "tutor": True,
            },
        )
        data2 = register2.json()
        user_token2 = data2["token"]

        start_time = default_start
        end_time = start_time + timedelta(minutes=60)
        client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {user_token1}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Physics",
            },
        )
        res = client.get(
            "/lessons", headers={"Authorization": f"Bearer {user_token2}"}
        ).json()

        assert len(res) == 0

