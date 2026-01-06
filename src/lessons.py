import helpers
import dataStore as ds

# May extend in future to make sure time is in the future
# But we can simply make the frontend such that it only shows possible times
def create_lesson(token: str, lesson_data) -> dict:

    decoded_token = helpers.decode_jwt_token(token)
    user_data = helpers.find_user_info(decoded_token)

    if user_data["role"] != "tutor":
        raise PermissionError("Only tutors can create lessons")
    
    delta = lesson_data.end_time - lesson_data.start_time
    duration = delta.total_seconds()/60
    
    if duration <= 0:
        raise ValueError("Invalid time frame")
    
    lesson_id = helpers.get_next_lesson_id()

    lesson = {
        "lesson_id": lesson_id,
        "start_time": lesson_data.start_time,
        "end_time": lesson_data.end_time,
        "duration": duration,
        "subject": lesson_data.subject,
        "tutor_email": user_data["email"],
        "student_email": None,
        "status": "Available"
    }
    
    ds.get_data()["lessons"].append(lesson)
    user_data["enrolled_lessons"].append(lesson)

    return lesson
