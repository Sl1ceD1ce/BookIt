import os
import pytest
import dataStore as ds
from server import app
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from helpers import decode_jwt_token
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
newStart = datetime(2026, 1, 7, 8, 0)  # 2026-01-06 08:00:00
newEnd = newStart + timedelta(minutes=60)

sampleLesson = {
    "start_time": startTime.isoformat(),
    "end_time": endTime.isoformat(),
    "subject": "Math",
}

class TestLessonDelete:
    def test_successfulLessonTutorUpdateV1(self, reset_data):
        tutorToken, lessonJson, studentToken = standardTutorStudentLesson(
            client, sampleTutor, sampleLesson, sampleStudent
        )

        lessonData = lessonJson.json()

        deleteRes = client.delete(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {tutorToken}"}
        )

        if deleteRes.status_code != 200:
            print(deleteRes.json())