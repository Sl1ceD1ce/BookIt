import helpers
import dataStore as ds
from fastapi import HTTPException
from datetime import datetime

# May extend in future to make sure time is in the future
# But we can simply make the frontend such that it only shows possible times
def create_lesson(token: str, lesson_data) -> dict:

    if helpers.is_token_blacklisted(token):
        raise ValueError("token is invalid")
    
    decoded_token = helpers.decode_jwt_token(token)
    user_data = helpers.find_user_info(decoded_token)

    if not user_data:
        raise ValueError("user does not exist")

    if user_data["role"] != "tutor":
        raise PermissionError("Only tutors can create lessons")
    
    delta = lesson_data.end_time - lesson_data.start_time
    duration = delta.total_seconds()/60
    
    if duration <= 0:
        raise HTTPException(status_code=400, detail="Invalid lesson duration")

    existing_lessons = []
    for lesson in ds.get_data()["lessons"]:
        if lesson["tutor_email"] == user_data["email"]:
            existing_lessons.append(lesson)

    for lesson in existing_lessons:
        existing_start = datetime.fromisoformat(lesson["start_time"])
        existing_end = datetime.fromisoformat(lesson["end_time"])

        if (lesson_data.start_time < existing_end and existing_start < lesson_data.end_time):
            raise HTTPException(status_code=400, detail="Lesson overlaps with existing lesson")
    
    lesson_id = helpers.get_next_lesson_id()

    lesson = {
        "lesson_id": lesson_id,
        "start_time": lesson_data.start_time.isoformat(),
        "end_time": lesson_data.end_time.isoformat(),
        "duration": duration,
        "subject": lesson_data.subject,
        "tutor_email": user_data["email"],
        "student_email": None,
        "status": "Available"
    }
    
    ds.get_data()["lessons"].append(lesson)
    user_data["enrolled_lessons"].append(lesson)

    return lesson

def get_user_lessons(token: str) -> list:
    if helpers.is_token_blacklisted(token):
        raise ValueError("token is invalid")

    decoded_token = helpers.decode_jwt_token(token)
    user_data = helpers.find_user_info(decoded_token)

    if not user_data:
        raise ValueError("user does not exist")

    user_email = user_data["email"]

    # Filter lessons where the user is tutor or student
    lessons = []
    for lesson in ds.get_data()["lessons"]:
        if lesson["tutor_email"] == user_email or lesson["student_email"] == user_email:
            lessons.append({
                "lesson_id": lesson["lesson_id"],
                "start_time": lesson["start_time"],
                "end_time": lesson["end_time"],
                "duration": lesson["duration"],
                "subject": lesson["subject"],
                "tutor_email": lesson["tutor_email"],
                "student_email": lesson["student_email"],
                "status": lesson["status"]
            })

    return lessons