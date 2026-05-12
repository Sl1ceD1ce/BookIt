"""Functions that perform updates, create and delete for lessons"""

from datetime import datetime

# pylint: disable=import-error
from fastapi import HTTPException
import helpers
import data_store as ds
from schemas import LessonCreate, LessonUpdate


# May extend in future to make sure time is in the future
# But we can simply make the frontend such that it only shows possible times
def create_lesson(token: str, lesson_data: LessonCreate) -> dict:
    """Creates a lesson given that the user is a tutor"""
    user_data = helpers.validate_and_get_user(token)

    if user_data["role"] != "tutor":
        raise PermissionError("Only tutors can create lessons")

    if not helpers.is_valid_datetime(lesson_data.start_time):
        raise ValueError("start time is in invalid format")

    if not helpers.is_valid_datetime(lesson_data.end_time):
        raise ValueError("end time is in invalid format")

    delta = datetime.fromisoformat(lesson_data.end_time) - datetime.fromisoformat(
        lesson_data.start_time
    )
    duration = int(delta.total_seconds() / 60)

    if datetime.fromisoformat(lesson_data.start_time) < datetime.now():
        raise HTTPException(status_code=400, detail="Lesson cannot start in the past")

    if duration <= 0:
        raise HTTPException(status_code=400, detail="Invalid lesson duration")

    lesson_data_dict = {
        "start_time": lesson_data.start_time,
        "end_time": lesson_data.end_time,
        "subject": lesson_data.subject,
    }

    lesson_id = helpers.generate_id()
    helpers.check_lesson_time(user_data, lesson_data_dict, lesson_id)

    lesson = {
        "lesson_id": lesson_id,
        "start_time": lesson_data.start_time,
        "end_time": lesson_data.end_time,
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
    """Gets an individual users corresponding lessons"""
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
        if user_id in (lesson["tutor_id"], lesson["assigned_student_id"]):
            lessons.append(
                {
                    "lesson_id": lesson["lesson_id"],
                    "start_time": lesson["start_time"],
                    "end_time": lesson["end_time"],
                    "duration": lesson["duration"],
                    "subject": lesson["subject"],
                    "tutor_id": lesson["tutor_id"],
                    "assigned_student_id": lesson.get("assigned_student_id"),
                    "available": lesson["available"],
                }
            )

    return lessons


def book_lesson(token: str, lesson_id: str) -> dict:
    """Books a student into the gievn lesson"""
    user_data = helpers.validate_and_get_user(token)

    if user_data["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can book lessons")

    lesson_data = helpers.find_lesson_info(lesson_id)

    if not lesson_data:
        raise HTTPException(status_code=404, detail="Lesson does not exist")

    if lesson_data["available"] is False:
        raise HTTPException(status_code=409, detail="Lesson is already booked")

    lesson_data["assigned_student_id"] = user_data["id"]
    lesson_data["available"] = False

    if datetime.fromisoformat(str(lesson_data["start_time"])) < datetime.now():
        raise HTTPException(
            status_code=400, detail="Lesson in the past cannot be booked"
        )

    return {
        "lesson_id": lesson_data["lesson_id"],
        "start_time": lesson_data["start_time"],
        "end_time": lesson_data["end_time"],
        "duration": lesson_data["duration"],
        "subject": lesson_data["subject"],
        "tutor_id": lesson_data["tutor_id"],
        "assigned_student_id": lesson_data.get("assigned_student_id"),
        "available": lesson_data["available"],
    }


def update_lesson(token: str, lesson_id: str, update_data: LessonUpdate) -> dict:
    """Updates a lesson depending on if the given user is a student or tutor"""
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

        lesson_data["assigned_student_id"] = update_data.assigned_student_id
        lesson_data["available"] = update_data.available

        return lesson_data

    if user_data["role"] == "tutor":

        if update_data.start_time is not None:
            lesson_data["start_time"] = update_data.start_time.isoformat()
        if update_data.end_time is not None:
            lesson_data["end_time"] = update_data.end_time.isoformat()
        if update_data.subject is not None:
            lesson_data["subject"] = update_data.subject

        # Always update student_email and status (even if None)
        lesson_data["assigned_student_id"] = update_data.assigned_student_id
        lesson_data["available"] = update_data.available

        helpers.check_lesson_time(user_data, lesson_data, lesson_id)

        return lesson_data

    raise HTTPException(status_code=401, detail="User has invalid role")


def delete_lesson(token: str, lesson_id: str) -> dict:
    """Deletes a lesson from data"""
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
