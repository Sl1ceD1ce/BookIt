import os
import pytest
import data_store as ds
from server import app
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from helper_testFunctions import standardTutorLesson, standardTutorStudentLesson
import helpers

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

startTime = default_start  # 2026-01-06 08:00:00
endTime = startTime + timedelta(minutes=60)
newStart = default_start + timedelta(days=1)  # 2026-01-06 08:00:00
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
                "assigned_student_id": None,
                "available": True,
            },
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
        assert lessons[0]["subject"] == "Physics"
        assert lessons[0]["start_time"] == newStart.isoformat()
        assert lessons[0]["end_time"] == newEnd.isoformat()
        assert lessons[0]["tutor_id"] == helpers.decode_jwt_token(tutorToken)["user_id"]
        assert lessons[0]["assigned_student_id"] is None
        assert lessons[0]["available"] == True

    def test_successfulLessonStudentUpdate(self, reset_data):
        tutorToken, lessonJson, studentToken = standardTutorStudentLesson(
            client, sampleTutor, sampleLesson, sampleStudent
        )

        lessonData = lessonJson.json()

        assert lessonData["available"] == False
        assert lessonData["assigned_student_id"] == helpers.decode_jwt_token(studentToken)["user_id"]

        patchRes = client.patch(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {studentToken}"},
            json={"assigned_student_id": None, "available": True},
        )

        assert patchRes.status_code == 200
        patchRes = patchRes.json()

        getRes = client.get(
            "/lessons", headers={"Authorization": f"Bearer {tutorToken}"}
        )

        assert getRes.status_code == 200
        lessons = getRes.json()

        getRes2 = client.get(
            "/lessons", headers={"Authorization": f"Bearer {studentToken}"}
        )
        assert getRes2.status_code == 200
        lessons2 = getRes2.json()

        assert len(lessons2) == 0

        assert len(lessons) == 1
        assert lessons[0]["lesson_id"] == lessonData["lesson_id"]
        assert lessons[0]["subject"] == "Math"
        assert lessons[0]["start_time"] == startTime.isoformat()
        assert lessons[0]["end_time"] == endTime.isoformat()
        assert lessons[0]["tutor_id"] == helpers.decode_jwt_token(tutorToken)["user_id"]
        assert lessons[0]["assigned_student_id"] is None
        assert lessons[0]["available"] == True

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
            headers={"Authorization": "Bearer fakeToken123"},
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
            "/lessons/1394819509158",
            headers={"Authorization": f"Bearer {tutorToken}"},
            json={
                "start_time": newStart.isoformat(),
                "end_time": newEnd.isoformat(),
                "subject": "Physics",
            },
        )

        assert patchRes.status_code == 404

    def test_updateDoesntChangeOtherLessons(self, reset_data):
        tutorToken, lessonJson, studentToken = standardTutorStudentLesson(
            client, sampleTutor, sampleLesson, sampleStudent
        )

        lesson2 = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {tutorToken}"},
            json={
                "start_time": newStart.isoformat(),
                "end_time": newEnd.isoformat(),
                "subject": "English",
            },
        )

        lessonData = lessonJson.json()
        lessonData2 = lesson2.json()

        patchRes = client.patch(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {tutorToken}"},
            json={
                "start_time": (startTime + timedelta(days=2)).isoformat(),
                "end_time": (endTime + timedelta(days=2)).isoformat(),
                "subject": "Physics",
                "assigned_student_id": None,
                "available": True,
            },
        )

        assert patchRes.status_code == 200
        patchRes = patchRes.json()

        getRes = client.get(
            "/lessons", headers={"Authorization": f"Bearer {tutorToken}"}
        )

        assert getRes.status_code == 200
        lessons = getRes.json()

        assert len(lessons) == 2
        assert lessons[1]["lesson_id"] == lessonData2["lesson_id"]
        assert lessons[1]["subject"] == "English"
        assert lessons[1]["start_time"] == newStart.isoformat()
        assert lessons[1]["end_time"] == newEnd.isoformat()
        assert lessons[1]["tutor_id"] == helpers.decode_jwt_token(tutorToken)["user_id"]
        assert lessons[1]["assigned_student_id"] is None
        assert lessons[1]["available"] == True
    
    def test_unsuccessfulUpdateOverlap(self, reset_data):
        tutorToken, lessonJson, studentToken = standardTutorStudentLesson(
            client, sampleTutor, sampleLesson, sampleStudent
        )

        lesson2 = client.post(
            "/lessons/",
            headers={"Authorization": f"Bearer {tutorToken}"},
            json={
                "start_time": newStart.isoformat(),
                "end_time": newEnd.isoformat(),
                "subject": "English",
            },
        )

        lessonData = lessonJson.json()
        lessonData2 = lesson2.json()

        patchRes = client.patch(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {tutorToken}"},
            json={
                "start_time": (newStart + timedelta(minutes=30)).isoformat(),
                "end_time": newEnd.isoformat(),
                "subject": "Physics",
                "assigned_student_id": None,
                "available": True,
            },
        )

        assert patchRes.status_code == 400