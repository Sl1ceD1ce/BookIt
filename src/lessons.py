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
    duration = int(delta.total_seconds() / 60)

    if duration <= 0:
        raise HTTPException(status_code=400, detail="Invalid lesson duration")

    existing_lessons = []
    for lesson in ds.get_data()["lessons"]:
        if lesson["tutor_id"] == user_data["id"]:
            existing_lessons.append(lesson)

    for lesson in existing_lessons:
        existing_start = datetime.fromisoformat(lesson["start_time"])
        existing_end = datetime.fromisoformat(lesson["end_time"])

        if (lesson_data.start_time < existing_end and existing_start < lesson_data.end_time):
            raise HTTPException(status_code=400, detail="Lesson overlaps with existing lesson")
    
    lesson_id = helpers.generate_id()

    lesson = {
        "lesson_id": lesson_id,
        "start_time": lesson_data.start_time.isoformat(),
        "end_time": lesson_data.end_time.isoformat(),
        "duration": duration,
        "subject": lesson_data.subject,
        "tutor_id": user_data["id"],
        "assigned_student_id": None,
        "available": True,
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

    user_id = decoded_token["user_id"]

    # Filter lessons where the user is tutor or student
    lessons = []
    for lesson in ds.get_data()["lessons"]:
        if lesson["tutor_id"] == user_id or lesson["student_id"] == user_id:
            lessons.append(
                {
                    "lesson_id": lesson["lesson_id"],
                    "start_time": lesson["start_time"],
                    "end_time": lesson["end_time"],
                    "duration": lesson["duration"],
                    "subject": lesson["subject"],
                    "tutor_id": lesson["tutor_id"],
                    "student_id": lesson.get("student_id"),
                    "available": lesson["available"],
                }
            )

    return lessons


def book_lesson(token: str, lesson_id: str) -> dict:
    if helpers.is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token is invalid")

    decoded_token = helpers.decode_jwt_token(token)
    user_data = helpers.find_user_info(decoded_token)

    if not user_data:
        raise HTTPException(status_code=401, detail="User does not exist")

    if user_data["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can book lessons")

    lesson_data = helpers.find_lesson_info(lesson_id)

    if not lesson_data:
        raise HTTPException(status_code=404, detail="Lesson does not exist")

    if lesson_data["available"] == False:
        raise HTTPException(status_code=409, detail="Lesson is already booked")

    lesson_data["student_id"] = user_data["id"]
    lesson_data["available"] = False

    return {
        "lesson_id": lesson_data["lesson_id"],
        "start_time": lesson_data["start_time"],
        "end_time": lesson_data["end_time"],
        "duration": lesson_data["duration"],
        "subject": lesson_data["subject"],
        "tutor_id": lesson_data["tutor_id"],
        "student_id": lesson_data.get("student_id"),
        "available": lesson_data["available"],
    }


def update_lesson(token: str, lesson_id: str, update_data) -> dict:
    if helpers.is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token is invalid")

    decoded_token = helpers.decode_jwt_token(token)
    user_data = helpers.find_user_info(decoded_token)
    lesson_data = helpers.find_lesson_info(lesson_id)

    if not user_data:
        raise HTTPException(status_code=401, detail="User does not exist")

    if not lesson_data:
        raise HTTPException(status_code=404, detail="Lesson does not exist")

    if user_data["role"] == "student":
        if update_data.start_time or update_data.end_time or update_data.subject:
            raise HTTPException(status_code=403, detail="Only tutors can modify this")

        # TODO: After transferring lessons to be id based instead of email based
        # Make it such that we validate that the student has this tutor as a tutor

        lesson_data["student_id"] = update_data.student_id
        lesson_data["available"] = update_data.available

        return lesson_data
    elif user_data["role"] == "tutor":
        if update_data.start_time is not None:
            lesson_data["start_time"] = update_data.start_time.isoformat()
        if update_data.end_time is not None:
            lesson_data["end_time"] = update_data.end_time.isoformat()
        if update_data.subject is not None:
            lesson_data["subject"] = update_data.subject
        # Always update student_email and status (even if None)
        lesson_data["student_id"] = update_data.student_id
        lesson_data["available"] = update_data.available

        return lesson_data
    else:
        raise HTTPException(status_code=401, detail="User has invalid role")


def delete_lesson(token: str, lesson_id: str) -> dict:
    if helpers.is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token is invalid")

    decoded_token = helpers.decode_jwt_token(token)
    user_data = helpers.find_user_info(decoded_token)
    lesson_data = helpers.find_lesson_info(lesson_id)

    if not user_data:
        raise HTTPException(status_code=401, detail="User does not exist")

    if not lesson_data:
        raise HTTPException(status_code=404, detail="Lesson does not exist")

    if user_data["role"] == "student":
        raise HTTPException(status_code=403, detail="Only tutors can modify this")

    if user_data["id"] != lesson_data["tutor_id"]:
        raise HTTPException(status_code=403, detail="User does not own lesson")
    
    helpers.get_lessons().remove(lesson_data)

    return {"message": "lesson deleted successfully"}
    

