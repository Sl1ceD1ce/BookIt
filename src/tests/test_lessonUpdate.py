from helpers import decode_jwt_token

class TestLessonUpdate:
    def test_successful_delete_with_booked_student(self, client, booked_lesson):
        tutor_token, student_token, lesson = booked_lesson
 
        res = client.delete(
            f"/lessons/{lesson['lesson_id']}",
            headers={"Authorization": f"Bearer {tutor_token}"},
        )
        assert res.status_code == 200
 
        assert client.get("/lessons", headers={"Authorization": f"Bearer {tutor_token}"}).json() == []
        assert client.get("/lessons", headers={"Authorization": f"Bearer {student_token}"}).json() == []
 
    def test_successful_delete_unbooked_lesson(self, client, tutor_token, lesson_id):
        res = client.delete(f"/lessons/{lesson_id}", headers={"Authorization": f"Bearer {tutor_token}"})
        assert res.status_code == 200
 
        lessons = client.get("/lessons", headers={"Authorization": f"Bearer {tutor_token}"}).json()
        assert lessons == []
 
    def test_correct_lesson_deleted(self, client, tutor_token, post_lesson, default_start, default_end):
        from datetime import timedelta
 
        res1 = post_lesson(tutor_token, default_start, default_end, subject="Math")
        res2 = post_lesson(tutor_token, default_start + timedelta(days=1), default_end + timedelta(days=1), subject="Physics")
        res3 = post_lesson(tutor_token, default_start + timedelta(days=2), default_end + timedelta(days=2), subject="English")
 
        id1 = res1.json()["lesson_id"]
        id2 = res2.json()["lesson_id"]
        id3 = res3.json()["lesson_id"]
 
        del_res = client.delete(f"/lessons/{id2}", headers={"Authorization": f"Bearer {tutor_token}"})
        assert del_res.status_code == 200
 
        lessons = client.get("/lessons", headers={"Authorization": f"Bearer {tutor_token}"}).json()
        returned_ids = [l["lesson_id"] for l in lessons]
 
        assert len(lessons) == 2
        assert id2 not in returned_ids
        assert id1 in returned_ids
        assert id3 in returned_ids
 
    def test_delete_nonexistent_lesson(self, client, tutor_token):
        res = client.delete("/lessons/fAKeID", headers={"Authorization": f"Bearer {tutor_token}"})
        assert res.status_code == 404
 
    def test_student_cannot_delete_lesson(self, client, booked_lesson):
        tutor_token, student_token, lesson = booked_lesson
 
        res = client.delete(
            f"/lessons/{lesson['lesson_id']}",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert res.status_code == 403
 
        tutor_lessons = client.get("/lessons", headers={"Authorization": f"Bearer {tutor_token}"}).json()
        student_lessons = client.get("/lessons", headers={"Authorization": f"Bearer {student_token}"}).json()
 
        assert len(tutor_lessons) == 1
        assert tutor_lessons[0]["lesson_id"] == lesson["lesson_id"]
        assert tutor_lessons[0]["assigned_student_id"] == decode_jwt_token(student_token)["user_id"]
        assert tutor_lessons[0]["available"] is False
        assert tutor_lessons == student_lessons
 
    def test_malformed_token(self, client, lesson_id):
        res = client.delete(f"/lessons/{lesson_id}", headers={"Authorization": "Bearer aifajoajga"})
        assert res.status_code == 401
 
    def test_logged_out_token_rejected(self, client, tutor_token, lesson_id):
        client.post("/users/logout", headers={"Authorization": f"Bearer {tutor_token}"})
        res = client.delete(f"/lessons/{lesson_id}", headers={"Authorization": f"Bearer {tutor_token}"})
        assert res.status_code == 401
 
    def test_tutor_cannot_delete_others_lesson(self, client, lesson_id, register_user):
        other_tutor = register_user(tutor=True, email="other@example.com", mobile="0412345679")
        res = client.delete(f"/lessons/{lesson_id}", headers={"Authorization": f"Bearer {other_tutor}"})
        assert res.status_code == 403