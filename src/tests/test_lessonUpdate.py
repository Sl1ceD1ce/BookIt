import os
import pytest
import dataStore as ds
from server import app
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from helper_testFunctions import standardTutorLesson, standardTutorStudentLesson

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

sampleLesson = {
    "start_time": startTime.isoformat(),
    "end_time": endTime.isoformat(),
    "subject": "Math",
}


class TestLessonUpdate:
    # TODO: Add more cases after smaller errors in previous functions are fixed

    def test_successfulLessonTutorUpdate(self, reset_data):
        # sets up a standard tutor instance and lesson instance
        tutorToken, lessonJson = standardTutorLesson(client, sampleTutor, sampleLesson)

        lessonData = lessonJson.json()

        newStart = datetime(2026, 1, 7, 8, 0)  # 2026-01-06 08:00:00
        newEnd = newStart + timedelta(minutes=60)

        patchRes = client.patch(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {tutorToken}"},
            json={
                "start_time": newStart.isoformat(),
                "end_time": newEnd.isoformat(),
                "subject": "Physics",
            },
        )

        patchRes = patchRes.json()
        assert patchRes.status_code == 200

        getRes = client.get(
            "/lessons", headers={"Authorization": f"Bearer {tutorToken}"}
        )

        assert getRes.status_code == 200
        lessons = getRes.json()

        assert len(lessons) == 1
        assert lessons[0]["lesson_id"] == lessonData["lesson_id"]
        assert lessons[0]["subject"] == "Physics"
        assert lessons[0]["start_time"] == newStart
        assert lessons[0]["end_time"] == newEnd
        assert lessons[0]["tutor_email"] == "john@example.com"
        assert lessons[0]["student_email"] is None
        assert lessons[0]["status"] == "Available"

    def test_successfulLessonStudentUpdate(self, reset_data):
        tutorToken, lessonJson, studentToken = standardTutorStudentLesson(
            client, sampleTutor, sampleLesson, studentToken
        )

        lessonData = lessonJson.json()

        

        patchRes = client.patch(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {tutorToken}"},
            json={
                
            },
        )

        


