from datetime import datetime, timedelta
import os
import pytest
import dataStore as ds
from server import app
from fastapi.testclient import TestClient
from helpers import decode_jwt_token
import helpers


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

# Test cases:
# Successful booking
# Unsuccessful booking with tutor
# Unsuccessful booking due to non-existent lesson
# Unsuccessful booking due to already being booked
# Unsuccessful booking due to non-existent student

class TestLessonBook:

    def test_successful_booking(self, reset_data):
        # Register tutor
        tutor_res = client.post(
            "/users/register",
            json={
                "first_name": "Jane",
                "last_name": "Tutor",
                "email": "jane@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        )
        tutor_token = tutor_res.json()["token"]

        # Register student
        student_res = client.post(
            "/users/register",
            json={
                "first_name": "Tom",
                "last_name": "Student",
                "email": "tom@example.com",
                "password": "Password123_",
                "mobile": "0498765432",
                "tutor": False,
            },
        )
        student_token = student_res.json()["token"]

        # Tutor creates a lesson
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=60)
        lesson_res = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Physics",
            },
        )
        assert lesson_res.status_code == 201
        lesson = lesson_res.json()

        # Student books the lesson
        book_url = f"/lessons/{lesson['lesson_id']}/book"
        print(f"Booking URL: {book_url}")

        book_res = client.post(
            book_url, headers={"Authorization": f"Bearer {student_token}"}
        )

        assert book_res.status_code == 200
        result = book_res.json()
        assert "lesson_id" in result
        assert result["start_time"] == start_time.isoformat()
        assert result["end_time"] == end_time.isoformat()
        assert result["duration"] == 60
        assert result["subject"] == "Physics"
        assert result["tutor_id"] == decode_jwt_token(tutor_token)["user_id"]
        assert result["assigned_student_id"] == decode_jwt_token(student_token)["user_id"]
        assert result["available"] == False

    def test_booking_with_tutor_forbidden(self, reset_data):
        # Register tutor
        tutor_res = client.post(
            "/users/register",
            json={
                "first_name": "Jane",
                "last_name": "Tutor",
                "email": "jane@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        )
        tutor_token = tutor_res.json()["token"]

        # Tutor creates a lesson
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=60)
        lesson_res = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Math",
            },
        )
        lesson = lesson_res.json()

        # Tutor tries to book their own lesson
        book_res = client.post(
            f"/lessons/{lesson['lesson_id']}/book",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert book_res.status_code == 403
        assert "Only students can book lessons" in book_res.json()["detail"]

    def test_booking_nonexistent_lesson(self, reset_data):
        # Register student
        student_res = client.post(
            "/users/register",
            json={
                "first_name": "Tom",
                "last_name": "Student",
                "email": "tom@example.com",
                "password": "Password123_",
                "mobile": "0498765432",
                "tutor": False,
            },
        )
        student_token = student_res.json()["token"]

        # Attempt to book a lesson that doesn't exist
        book_res = client.post(
            "/lessons/999/book", headers={"Authorization": f"Bearer {student_token}"}
        )
        assert book_res.status_code == 404
        assert "Lesson does not exist" in book_res.json()["detail"]

    def test_booking_already_booked_lesson(self, reset_data):
        # Register tutor
        tutor_res = client.post(
            "/users/register",
            json={
                "first_name": "Jane",
                "last_name": "Tutor",
                "email": "jane@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        )
        tutor_token = tutor_res.json()["token"]

        # Register student
        student_res = client.post(
            "/users/register",
            json={
                "first_name": "Tom",
                "last_name": "Student",
                "email": "tom@example.com",
                "password": "Password123_",
                "mobile": "0498765432",
                "tutor": False,
            },
        )
        student_token = student_res.json()["token"]

        # Tutor creates a lesson
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=60)
        lesson_res = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Chemistry",
            },
        )
        lesson = lesson_res.json()

        # First booking succeeds
        book_res1 = client.post(
            f"/lessons/{lesson['lesson_id']}/book",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert book_res1.status_code == 200

        # Second booking attempt fails
        book_res2 = client.post(
            f"/lessons/{lesson['lesson_id']}/book",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert book_res2.status_code == 409
        assert "Lesson is already booked" in book_res2.json()["detail"]
    
    def test_booking_with_malformed_token(self, reset_data):
        # Register tutor
        tutor_res = client.post(
            "/users/register",
            json={
                "first_name": "Jane",
                "last_name": "Tutor",
                "email": "jane@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        )
        tutor_token = tutor_res.json()["token"]

        # Tutor creates a lesson
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=60)
        lesson_res = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Math",
            },
        )
        lesson = lesson_res.json()

        book_res = client.post(
            f"/lessons/{lesson['lesson_id']}/book",
            headers={"Authorization": "Bearer dsafasdfkj"},
        )
        assert book_res.status_code == 401

    def test_unsuccessful_booking_in_past(self, reset_data):
        # Register tutor
        tutor_res = client.post(
            "/users/register",
            json={
                "first_name": "Jane",
                "last_name": "Tutor",
                "email": "jane@example.com",
                "password": "Password123_",
                "mobile": "0412345678",
                "tutor": True,
            },
        )
        tutor_token = tutor_res.json()["token"]

        # Register student
        student_res = client.post(
            "/users/register",
            json={
                "first_name": "Tom",
                "last_name": "Student",
                "email": "tom@example.com",
                "password": "Password123_",
                "mobile": "0498765432",
                "tutor": False,
            },
        )
        student_token = student_res.json()["token"]

        # Tutor creates a lesson
        start_time = datetime.now() + timedelta(hours=1)
        end_time = start_time + timedelta(minutes=60)
        lesson_res = client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "subject": "Physics",
            },
        )
        assert lesson_res.status_code == 201
        lesson = lesson_res.json()
        
        lesson_info = helpers.find_lesson_info(lesson['lesson_id'])
        lesson_info["start_time"] = datetime.now() - timedelta(hours=1)
        # Student books the lesson
        book_url = f"/lessons/{lesson['lesson_id']}/book"
        print(f"Booking URL: {book_url}")

        book_res = client.post(
            book_url, headers={"Authorization": f"Bearer {student_token}"}
        )

        assert book_res.status_code == 400