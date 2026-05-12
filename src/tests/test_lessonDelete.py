import os
import pytest
import datastore as ds
from server import app
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from helpers import decode_jwt_token
import helper_testFunctions

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

sampleTutor2 = {
    "first_name": "Richard",
    "last_name": "Zhang",
    "email": "richardzhang@gmail.com",
    "password": "LigmaBalls123_",
    "mobile": "0419491812",
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

startTime = datetime.now() + timedelta(minutes=60)  # 2026-01-06 08:00:00
endTime = startTime + timedelta(minutes=60)
startTime2 = startTime + timedelta(days=1)  # 2026-01-07 08:00:00
endTime2 = startTime2 + timedelta(minutes=60)
startTime3 = startTime + timedelta(hours=2)  # 2026-01-07 10:00:00
endTime3 = startTime3 + timedelta(minutes=60)

sampleLesson = {
    "start_time": startTime.isoformat(),
    "end_time": endTime.isoformat(),
    "subject": "Math",
}

sampleLesson2 = {
    "start_time": startTime2.isoformat(),
    "end_time": endTime2.isoformat(),
    "subject": "Physics",
}

sampleLesson3 = {
    "start_time": startTime3.isoformat(),
    "end_time": endTime3.isoformat(),
    "subject": "English",
}

sampleLessons = [sampleLesson, sampleLesson2, sampleLesson3]

class TestLessonDelete:
    def test_successfulLessonDeleteV1(self, reset_data):
        tutorToken, lessonJson, studentToken = helper_testFunctions.standardTutorStudentLesson(
            client, sampleTutor, sampleLesson, sampleStudent
        )

        lessonData = lessonJson.json()

        deleteRes = client.delete(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {tutorToken}"}
        )

        assert deleteRes.status_code == 200

        tutorLessonRes = client.get("/lessons",
            headers={"Authorization": f"Bearer {tutorToken}"})
        
        studentLessonRes = client.get("/lessons",
            headers={"Authorization": f"Bearer {studentToken}"})
        
        assert tutorLessonRes.status_code == 200
        assert tutorLessonRes.status_code == 200

        tutorLessonRes = tutorLessonRes.json()
        studentLessonRes = studentLessonRes.json()

        assert tutorLessonRes == [] 
        assert studentLessonRes == []


    def test_successfulLessonDeleteV2(self, reset_data):
        tutorToken, lessonJson = helper_testFunctions.standardTutorLesson(
            client, sampleTutor, sampleLesson
        )

        lessonData = lessonJson.json()

        deleteRes = client.delete(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {tutorToken}"}
        )

        assert deleteRes.status_code == 200

        tutorLessonRes = client.get("/lessons",
            headers={"Authorization": f"Bearer {tutorToken}"})
        
        assert tutorLessonRes.status_code == 200
        tutorLessonRes = tutorLessonRes.json()
        assert tutorLessonRes == [] 


    def test_correctDelete(self, reset_data):
        tutorToken, lessonResponses = helper_testFunctions.tutorLessons(
            client, sampleTutor, sampleLessons
        )

        deletedLessonId = lessonResponses[1]['lesson_id']
        remainingLessonIds = [lessonResponses[0]['lesson_id'], lessonResponses[2]['lesson_id']]

        deleteRes = client.delete(
            f"/lessons/{lessonResponses[1]['lesson_id']}",
            headers={"Authorization": f"Bearer {tutorToken}"}
        )

        assert deleteRes.status_code == 200

        tutorLessonRes = client.get("/lessons",
            headers={"Authorization": f"Bearer {tutorToken}"})
        
        lessons = tutorLessonRes.json()

        assert len(lessons) == 2
    
        returnedLessonIds = [lesson['lesson_id'] for lesson in lessons]
        assert lessonResponses[1]['lesson_id'] not in returnedLessonIds
    
        # Verify the correct lessons remain
        assert remainingLessonIds[0] in returnedLessonIds
        assert remainingLessonIds[1] in returnedLessonIds
    
        # Verify all remaining lessons are correct
        assert set(returnedLessonIds) == set(remainingLessonIds)
        
        
    def test_deleteNonExistentLesson(self, reset_data):
        register = client.post("/users/register", json=sampleTutor)
        data = register.json()
        userToken = data["token"]

        deleteRes = client.delete(
            "/lessons/fAKeID",
            headers={"Authorization": f"Bearer {userToken}"}
        )

        assert deleteRes.status_code == 404


    def test_studentDeleteLesson(self, reset_data):
        tutorToken, lessonJson, studentToken = helper_testFunctions.standardTutorStudentLesson(
            client, sampleTutor, sampleLesson, sampleStudent
        )

        lessonData = lessonJson.json()

        deleteRes = client.delete(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {studentToken}"}
        )

        assert deleteRes.status_code == 403

        tutorLessonRes = client.get("/lessons",
            headers={"Authorization": f"Bearer {tutorToken}"})
        
        studentLessonRes = client.get("/lessons",
            headers={"Authorization": f"Bearer {studentToken}"})

        tutorLessonRes = tutorLessonRes.json()
        studentLessonRes = studentLessonRes.json()

        assert len(tutorLessonRes) == 1
        assert tutorLessonRes[0]["lesson_id"] == lessonData["lesson_id"]
        assert tutorLessonRes[0]["subject"] == "Math"
        assert tutorLessonRes[0]["start_time"] == startTime.isoformat()
        assert tutorLessonRes[0]["end_time"] == endTime.isoformat()
        assert tutorLessonRes[0]["tutor_id"] == decode_jwt_token(tutorToken)["user_id"]
        assert tutorLessonRes[0]["assigned_student_id"] == decode_jwt_token(studentToken)["user_id"]
        assert tutorLessonRes[0]["available"] == False

        assert tutorLessonRes == studentLessonRes


    def test_malformedToken(self, reset_data):
        tutorToken, lessonJson, studentToken = helper_testFunctions.standardTutorStudentLesson(
            client, sampleTutor, sampleLesson, sampleStudent
        )

        lessonData = lessonJson.json()

        deleteRes = client.delete(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": "Bearer aifajoajga"}
        )

        assert deleteRes.status_code == 401


    def test_expiredToken(self, reset_data):
        tutorToken, lessonJson, studentToken = helper_testFunctions.standardTutorStudentLesson(
            client, sampleTutor, sampleLesson, sampleStudent
        )

        logoutRes = client.post("/users/logout", headers={"Authorization": f"Bearer {tutorToken}"})

        assert logoutRes.status_code == 200

        lessonData = lessonJson.json()

        deleteRes = client.delete(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {tutorToken}"}
        )

        assert deleteRes.status_code == 401

    def test_tutorDoesNotOwnLesson(self, reset_data):
        tutorToken, lessonJson = helper_testFunctions.standardTutorLesson(
            client, sampleTutor, sampleLesson
        )

        lessonData = lessonJson.json()

        tutor2Res = client.post("/users/register", json=sampleTutor2)
        tutorToken2 = tutor2Res.json()["token"]

        deleteRes = client.delete(
            f"/lessons/{lessonData['lesson_id']}",
            headers={"Authorization": f"Bearer {tutorToken2}"}
        )

        assert deleteRes.status_code == 403

