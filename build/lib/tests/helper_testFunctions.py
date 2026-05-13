from server import app
from fastapi.testclient import TestClient

def standardTutorLesson(client: TestClient, tutorInput: object, lessonInput: object):
    """Creates a standard tutor and lesson instance"""

    register = client.post("/users/register", json=tutorInput)
    
    data = register.json()
    userToken = data["token"]

    lessonRes = client.post(
        "/lessons",
        headers={"Authorization": f"Bearer {userToken}"},
        json=lessonInput)
    
    return userToken, lessonRes

def standardTutorStudentLesson(client: TestClient, tutorInput: object, lessonInput: object, studentInput: object):
    """Creates a tutor, student and lesson with a student booked into the lesson created by the tutor"""

    tutorToken, lessonRes = standardTutorLesson(client, tutorInput, lessonInput)

    studentRegister = client.post("/users/register", json=studentInput)
    lesson = lessonRes.json()

    studentData = studentRegister.json()
    studentToken = studentData["token"]

    bookRes = client.post(
        f"/lessons/{lesson['lesson_id']}/book", headers={"Authorization": f"Bearer {studentToken}"}
    )

    return tutorToken, bookRes, studentToken

def tutorLessons(client: TestClient, tutorInput: object, lessonInputs: list):
    """Creates a tutor and X amount of lessons. Where X is the number of lessonInputs"""

    register = client.post("/users/register", json=tutorInput)
    
    data = register.json()
    userToken = data["token"]

    lessonResponses = list()

    for lessonInput in lessonInputs:
        lessonResponses.append(client.post(
            "/lessons",
            headers={"Authorization": f"Bearer {userToken}"},
            json=lessonInput).json())
    
    return userToken, lessonResponses
        