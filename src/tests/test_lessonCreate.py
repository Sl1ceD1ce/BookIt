<<<<<<< HEAD
import os
import pytest
import data_store as ds
from server import app
from fastapi.testclient import TestClient
=======
>>>>>>> c58886ee518fd6d96d10b7cde49e291958771f97
from datetime import datetime, timedelta
from helpers import decode_jwt_token

class TestLessonCreate:

    def test_successful_lesson_creation(self, client, tutor_token, post_lesson, 
                                        default_start, default_end):
        res = post_lesson(tutor_token, default_start, default_end)
        data = res.json()

        assert res.status_code == 201
        assert "lesson_id" in data
        assert data["start_time"] == default_start.isoformat()
        assert data["end_time"] == default_end.isoformat()
        assert data["duration"] == 60
        assert data["subject"] == "Math"
        assert data["tutor_id"] == decode_jwt_token(tutor_token)["user_id"]
        assert data["assigned_student_id"] is None
        assert data["available"] is True


    def test_invalid_token(self, post_lesson, default_start, default_end):
        res = post_lesson("sdfsdfg", default_start, default_end)
        assert res.status_code == 401

    def test_student_cannot_create_lesson(self, post_lesson, student_token, default_start, default_end):
        res = post_lesson(student_token, default_start, default_end, subject="English")
        assert res.status_code == 403

    def test_invalid_duration(self, post_lesson, tutor_token, default_start):
        end = default_start - timedelta(minutes=20)
        res = post_lesson(tutor_token, default_start, end)
        assert res.status_code == 400

    def test_overlap_rejected(self, post_lesson, tutor_token, default_start, default_end):
        assert post_lesson(tutor_token, default_start, default_end).status_code == 201
 
        start2 = default_start + timedelta(minutes=30)
        res2 = post_lesson(tutor_token, start2, start2 + timedelta(minutes=60), subject="History")
        assert res2.status_code in (400, 409)
        assert "overlaps" in res2.json()["detail"].lower()

    def test_boundary_lessons_allowed(self, post_lesson, tutor_token, default_start, default_end):
        assert post_lesson(tutor_token, default_start, default_end).status_code == 201
        assert post_lesson(tutor_token, default_end, default_end + timedelta(minutes=60), subject="History").status_code == 201
 
    def test_same_time_different_tutors_allowed(self, post_lesson, register_user, default_start, default_end):
        token1 = register_user(tutor=True, email="t1@example.com", mobile="0412345678")
        token2 = register_user(tutor=True, email="t2@example.com", mobile="0412345679")
        assert post_lesson(token1, default_start, default_end).status_code == 201
        assert post_lesson(token2, default_start, default_end).status_code == 201
 
    def test_lesson_in_the_past_rejected(self, post_lesson, tutor_token):
        start = datetime.now() - timedelta(minutes=30)
        assert post_lesson(tutor_token, start, start + timedelta(minutes=60)).status_code == 400
 
    def test_invalid_month_in_start_time(self, client, tutor_token):
        res = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "start_time": "2026-14-06T09:00:00",
                "end_time": datetime(2026, 1, 6, 9, 0).isoformat(),
                "subject": "Math",
            },
        )
        assert res.status_code == 401
 
    def test_incomplete_datetime_format(self, client, tutor_token):
        res = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "start_time": "2026-03",
                "end_time": datetime(2026, 1, 6, 9, 0).isoformat(),
                "subject": "Math",
            },
        )
        assert res.status_code == 401
 
    def test_empty_start_time(self, client, tutor_token):
        res = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {tutor_token}"},
            json={
                "start_time": "",
                "end_time": datetime(2026, 1, 6, 9, 0).isoformat(),
                "subject": "Math",
            },
        )
        assert res.status_code == 401