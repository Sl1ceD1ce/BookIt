from datetime import datetime, timedelta

from database import Lesson
from helpers import decode_jwt_token

class TestLessonBook:

    def test_successful_booking(self, client, tutor_token, student_token, lesson_id, default_start, default_end):
        res = client.post(f"/lessons/{lesson_id}/book", headers={"Authorization": f"Bearer {student_token}"})
        assert res.status_code == 200
        result = res.json()
 
        assert "lesson_id" in result
        assert result["start_time"] == default_start.isoformat()
        assert result["end_time"] == default_end.isoformat()
        assert result["duration"] == 60
        assert result["subject"] == "Math"
        assert result["tutor_id"] == decode_jwt_token(tutor_token)["user_id"]
        assert result["assigned_student_id"] == decode_jwt_token(student_token)["user_id"]
        assert result["available"] is False
 
    def test_booking_with_tutor_forbidden(self, client, tutor_token, lesson_id):
        res = client.post(f"/lessons/{lesson_id}/book", headers={"Authorization": f"Bearer {tutor_token}"})
        assert res.status_code == 403
        assert "Only students can book lessons" in res.json()["detail"]
 
    def test_booking_nonexistent_lesson(self, client, student_token):
        res = client.post("/lessons/nonexistent-id/book", headers={"Authorization": f"Bearer {student_token}"})
        assert res.status_code == 404
        assert "Lesson does not exist" in res.json()["detail"]
 
    def test_booking_already_booked_lesson(self, client, student_token, lesson_id):
        res1 = client.post(f"/lessons/{lesson_id}/book", headers={"Authorization": f"Bearer {student_token}"})
        assert res1.status_code == 200
 
        res2 = client.post(f"/lessons/{lesson_id}/book", headers={"Authorization": f"Bearer {student_token}"})
        assert res2.status_code == 409
        assert "Lesson is already booked" in res2.json()["detail"]
 
    def test_booking_with_malformed_token(self, client, lesson_id):
        res = client.post(f"/lessons/{lesson_id}/book", headers={"Authorization": "Bearer dsafasdfkj"})
        assert res.status_code == 401
 
    def test_unsuccessful_booking_in_past(self, client, student_token, lesson_id, db):
        # Directly set the lesson's start_time to the past via DB session
        lesson = db.get(Lesson, lesson_id)
        lesson.start_time = (datetime.now() - timedelta(hours=1)).isoformat()
        db.commit()
 
        res = client.post(f"/lessons/{lesson_id}/book", headers={"Authorization": f"Bearer {student_token}"})
        assert res.status_code == 400
 