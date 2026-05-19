<<<<<<< HEAD
import os
import pytest
import data_store as ds
from server import app
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
=======
from datetime import timedelta
>>>>>>> c58886ee518fd6d96d10b7cde49e291958771f97
from helpers import decode_jwt_token

class TestLessonGet:
    def test_get_tutor_lessons(self, client, tutor_token, post_lesson, default_start, default_end):
        res = post_lesson(tutor_token, default_start, default_end)
        assert res.status_code == 201
        lesson = res.json()
 
        get_res = client.get("/lessons", headers={"Authorization": f"Bearer {tutor_token}"})
        assert get_res.status_code == 200
        lessons = get_res.json()
 
        assert len(lessons) == 1
        assert lessons[0]["lesson_id"] == lesson["lesson_id"]
        assert lessons[0]["subject"] == "Math"
        assert lessons[0]["tutor_id"] == decode_jwt_token(tutor_token)["user_id"]
        assert lessons[0]["assigned_student_id"] is None
        assert lessons[0]["available"] is True

    def test_get_student_lessons_after_booking(self, client, booked_lesson):
        tutor_token, student_token, lesson = booked_lesson
 
        get_res = client.get("/lessons", headers={"Authorization": f"Bearer {student_token}"})
        assert get_res.status_code == 200
        lessons_list = get_res.json()
 
        assert len(lessons_list) == 1
        booked = lessons_list[0]
        assert booked["lesson_id"] == lesson["lesson_id"]
        assert booked["subject"] == "Math"
        assert booked["tutor_id"] == decode_jwt_token(tutor_token)["user_id"]
        assert booked["assigned_student_id"] == decode_jwt_token(student_token)["user_id"]
        assert booked["available"] is False
 
    def test_get_lessons_multiple_users(self, client, register_user, post_lesson, default_start, default_end):
        tutor1_token = register_user(tutor=True, email="t1@example.com", mobile="0412345671")
        tutor2_token = register_user(tutor=True, email="t2@example.com", mobile="0412345672")
        student1_token = register_user(tutor=False, email="s1@example.com", mobile="0412345673")
        student2_token = register_user(tutor=False, email="s2@example.com", mobile="0412345674")
 
        lesson1 = post_lesson(tutor1_token, default_start, default_end, subject="Physics").json()
        lesson2 = post_lesson(tutor2_token, default_start, default_end, subject="Chemistry").json()
 
        client.post(f"/lessons/{lesson1['lesson_id']}/book", headers={"Authorization": f"Bearer {student1_token}"})
        client.post(f"/lessons/{lesson2['lesson_id']}/book", headers={"Authorization": f"Bearer {student2_token}"})
 
        lessons1 = client.get("/lessons", headers={"Authorization": f"Bearer {student1_token}"}).json()
        lessons2 = client.get("/lessons", headers={"Authorization": f"Bearer {student2_token}"}).json()
 
        assert len(lessons1) == 1
        assert lessons1[0]["lesson_id"] == lesson1["lesson_id"]
        assert lessons1[0]["assigned_student_id"] == decode_jwt_token(student1_token)["user_id"]
 
        assert len(lessons2) == 1
        assert lessons2[0]["lesson_id"] == lesson2["lesson_id"]
        assert lessons2[0]["assigned_student_id"] == decode_jwt_token(student2_token)["user_id"]
 
    def test_get_student_lessons_multiple(self, client, tutor_token, student_token, post_lesson, default_start, default_end):
        lesson1 = post_lesson(tutor_token, default_start, default_end, subject="Physics").json()
        start2 = default_start + timedelta(hours=1)
        end2 = default_end + timedelta(hours=1)
        lesson2 = post_lesson(tutor_token, start2, end2, subject="Math").json()
 
        client.post(f"/lessons/{lesson1['lesson_id']}/book", headers={"Authorization": f"Bearer {student_token}"})
        client.post(f"/lessons/{lesson2['lesson_id']}/book", headers={"Authorization": f"Bearer {student_token}"})
 
        get_res = client.get("/lessons", headers={"Authorization": f"Bearer {student_token}"})
        assert get_res.status_code == 200
        assert len(get_res.json()) == 2
 
    def test_get_tutor_lessons_none(self, client, tutor_token):
        get_res = client.get("/lessons", headers={"Authorization": f"Bearer {tutor_token}"})
        assert get_res.status_code == 200
        assert len(get_res.json()) == 0
 
    def test_get_invalid_token(self, client):
        get_res = client.get("/lessons", headers={"Authorization": "Bearer fasdfasdf"})
        assert get_res.status_code == 401
 
    def test_get_logged_out(self, client, tutor_token):
        client.post("/users/logout", headers={"Authorization": f"Bearer {tutor_token}"})
        get_res = client.get("/lessons", headers={"Authorization": f"Bearer {tutor_token}"})
        assert get_res.status_code == 401
 
    def test_tutor_doesnt_see_other_lesson(self, client, register_user, post_lesson, default_start, default_end):
        tutor1_token = register_user(tutor=True, email="t1@example.com", mobile="0412345671")
        tutor2_token = register_user(tutor=True, email="t2@example.com", mobile="0412345672")
 
        post_lesson(tutor1_token, default_start, default_end, subject="Physics")
 
        res = client.get("/lessons", headers={"Authorization": f"Bearer {tutor2_token}"})
        assert len(res.json()) == 0

