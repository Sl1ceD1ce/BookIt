import os
import pytest
import dataStore as ds
from server import app
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from helper_testFunctions import standardTutorLesson, standardTutorStudentLesson
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


sampleTutor = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "password": "Password123_",
    "mobile": "0412345678",
    "tutor": True,
}

sampleStudent = {
    "first_name": "Jimmy",
    "last_name": "Butler",
    "email": "jimmybutler@example.com",
    "password": "Password435_",
    "mobile": "0412342149",
    "tutor": False,
}

startTime = datetime(2026, 1, 6, 8, 0)  # 2026-01-06 08:00:00
endTime = startTime + timedelta(minutes=60)
newStart = datetime(2026, 1, 7, 8, 0)  # 2026-01-06 08:00:00
newEnd = newStart + timedelta(minutes=60)

sampleLesson = {
    "start_time": startTime.isoformat(),
    "end_time": endTime.isoformat(),
    "subject": "Math",
}


class TestLessonUpdate:
    # TODO: Add more cases after smaller errors in previous functions are fixed

    def test_successfulLessonTutorUpdate(self, reset_data):
        # sets up a standard tutor instance and lesson instance
        tutorToken, lessonJson, studentToken = standardTutorStudentLesson(
            client, sampleTutor, sampleLesson, sampleStudent
        )

        lessonData = lessonJson.json()

        patchRes = client.patch(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {tutorToken}"},
            json={
                "start_time": newStart.isoformat(),
                "end_time": newEnd.isoformat(),
                "subject": "Physics",
                "student_id": None,
                "available": True,
            },
        )

        if patchRes.status_code != 200:
            print(patchRes.json())

        assert patchRes.status_code == 200
        patchRes = patchRes.json()

        getRes = client.get(
            "/lessons", headers={"Authorization": f"Bearer {tutorToken}"}
        )

        assert getRes.status_code == 200
        lessons = getRes.json()

        assert len(lessons) == 1
        assert lessons[0]["lesson_id"] == lessonData["lesson_id"]
        assert lessons[0]["subject"] == "Physics"
        assert lessons[0]["start_time"] == newStart.isoformat()
        assert lessons[0]["end_time"] == newEnd.isoformat()
        assert lessons[0]["tutor_id"] == helpers.decode_jwt_token(tutorToken)["user_id"]
        assert lessons[0]["student_id"] is None
        assert lessons[0]["available"] == True

    def test_successfulLessonStudentUpdate(self, reset_data):
        tutorToken, lessonJson, studentToken = standardTutorStudentLesson(
            client, sampleTutor, sampleLesson, sampleStudent
        )

        lessonData = lessonJson.json()

        assert lessonData["available"] == False
        assert lessonData["student_id"] == helpers.decode_jwt_token(studentToken)["user_id"]

        patchRes = client.patch(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {studentToken}"},
            json={"student_email": None, "available": False},
        )

        assert patchRes.status_code == 200
        patchRes = patchRes.json()

        getRes = client.get(
            "/lessons", headers={"Authorization": f"Bearer {tutorToken}"}
        )

        assert getRes.status_code == 200
        lessons = getRes.json()

        assert len(lessons) == 1
        assert lessons[0]["lesson_id"] == lessonData["lesson_id"]
        assert lessons[0]["subject"] == "Math"
        assert lessons[0]["start_time"] == startTime.isoformat()
        assert lessons[0]["end_time"] == endTime.isoformat()
        assert lessons[0]["tutor_id"] == helpers.decode_jwt_token(tutorToken)["user_id"]
        assert lessons[0]["student_id"] is None
        assert lessons[0]["available"] == False

    def test_wrongRole(self, reset_data):
        tutorToken, lessonJson, studentToken = standardTutorStudentLesson(
            client, sampleTutor, sampleLesson, sampleStudent
        )

        lessonData = lessonJson.json()

        patchRes = client.patch(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {studentToken}"},
            json={
                "start_time": newStart.isoformat(),
                "end_time": newEnd.isoformat(),
                "subject": "Physics",
            },
        )

        assert patchRes.status_code == 403

    def test_invalidToken(self, reset_data):
        tutorToken, lessonJson, studentToken = standardTutorStudentLesson(
            client, sampleTutor, sampleLesson, sampleStudent
        )

        lessonData = lessonJson.json()

        patchRes = client.patch(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {"fakeToken123"}"},
            json={
                "start_time": newStart.isoformat(),
                "end_time": newEnd.isoformat(),
                "subject": "Physics",
            },
        )

        assert patchRes.status_code == 401

    def test_nonExistentLesson(self, reset_data):
        tutorToken, lessonJson, studentToken = standardTutorStudentLesson(
            client, sampleTutor, sampleLesson, sampleStudent
        )

        lessonData = lessonJson.json()

        patchRes = client.patch(
            f"/lessons/{"1394819509158"}",
            headers={"Authorization": f"Bearer {tutorToken}"},
            json={
                "start_time": newStart.isoformat(),
                "end_time": newEnd.isoformat(),
                "subject": "Physics",
            },
        )

        assert patchRes.status_code == 404
