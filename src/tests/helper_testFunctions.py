from server import app
from fastapi.testclient import TestClient

def standardTutorLesson(client: TestClient, tutor_input: object, lesson_input: object):
    """Creates a standard tutor and lesson instance"""

    register = client.post("/users/register", json=tutor_input)
    
    data = register.json()
    userToken = data["token"]

    lessonRes = client.post(
        "/lessons",
        headers={"Authorization": f"Bearer {userToken}"},
        json=lesson_input)
    
    return userToken, lessonRes

def standardTutorStudentLesson(client: TestClient, tutor_input: object, lesson_input: object, student_input: object):
    tutorToken, lessonRes = standardTutorLesson(client, tutor_input, lesson_input)

    studentRegister = client.post("/users/register", json=student_input)
    lesson = lessonRes.json()

    studentData = studentRegister.json()
    studentToken = studentData["token"]

    bookRes = client.post(
        f"/lessons/{lesson['lesson_id']}/book", headers={"Authorization": f"Bearer {studentToken}"}
    )

    return tutorToken, bookRes, studentToken


# def standard_Tutor_Lesson():



# def standard_Student_Tutor_Lesson():