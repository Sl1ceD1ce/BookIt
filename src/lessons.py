import helpers
from fastapi import HTTPException
from datetime import datetime
from sqlalchemy.orm import Session, or_
from sqlalchemy import select

from database import Lesson


# May extend in future to make sure time is in the future
# But we can simply make the frontend such that it only shows possible times
def create_lesson(token: str, lesson_data, db: Session) -> dict:
    if helpers.is_token_blacklisted(token, db):
        raise ValueError("token is invalid")

    decoded_token = helpers.decode_jwt_token(token)
    user = helpers.find_user_info(decoded_token, db)

    if not user:
        raise ValueError("user does not exist")

    if user.role != "tutor":
        raise PermissionError("Only tutors can create lessons")

    if not helpers.is_valid_datetime(lesson_data.start_time):
        raise ValueError("start time is in invalid format")

    if not helpers.is_valid_datetime(lesson_data.end_time):
        raise ValueError("end time is in invalid format")
    
    start = datetime.fromisoformat(lesson_data.start_time)
    end = datetime.fromisoformat(lesson_data.end_time)

    if start < datetime.now():
        raise HTTPException(status_code=400, detail="Lesson cannot start in the past")
    
    duration = int((end - start).total_seconds() / 60)

    if duration <= 0:
        raise HTTPException(status_code=400, detail="Invalid lesson duration")

    lesson_id = helpers.generate_id()
    helpers.check_lesson_time(
        user_data=user,
        lesson_data={
            "start_time": lesson_data.start_time,
            "end_time": lesson_data.end_time
        },
        lesson_id=lesson_id,
        db=db
    )

    lesson = Lesson(
        id=lesson_id,
        start_time=lesson_data.start_time,
        end_time=lesson_data.end_time,
        subject=lesson_data.subject,
        duration=duration,
        tutor_id=user.id,
        assigned_student_id=None,
        available=True
    )

    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return {
        "lesson_id": lesson_id,
        "start_time": lesson_data.start_time,
        "end_time": lesson_data.end_time,
        "duration": duration,
        "subject": lesson_data.subject,
        "tutor_id": user["id"],
        "assigned_student_id": None,
        "available": True,
    }



def get_user_lessons(token: str, db: Session) -> list:
    if helpers.is_token_blacklisted(token, db):
        raise ValueError("token is invalid")

    decoded_token = helpers.decode_jwt_token(token)
    user = helpers.find_user_info(decoded_token, db)

    if not user :
        raise ValueError("user does not exist")

    user_id = decoded_token["user_id"]

    # Filter lessons where the user is tutor or student
    stmt = select(Lesson).where(
        or_(
            Lesson.tutor_id == user_id,
            Lesson.assigned_student_id == user_id
        )
    )
    lessons = db.execute(stmt).scalars().all()
    return [
        {
            "lesson_id": lesson.id,
            "start_time": lesson.start_time,
            "end_time": lesson.end_time,
            "duration": lesson.duration,
            "subject": lesson.subject,
            "tutor_id": lesson.tutor_id,
            "assigned_student_id": lesson.assigned_student_id,
            "available": lesson.available,
        }
        for lesson in lessons
    ]


def book_lesson(token: str, lesson_id: str, db: Session) -> dict:
    if helpers.is_token_blacklisted(token, db):
        raise HTTPException(status_code=401, detail="Token is invalid")

    decoded_token = helpers.decode_jwt_token(token)
    user = helpers.find_user_info(decoded_token, db)

    if not user:
        raise HTTPException(status_code=401, detail="User does not exist")

    if user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can book lessons")

    lesson = helpers.find_lesson_info(lesson_id, db)

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson does not exist")

    if not lesson.available:
        raise HTTPException(status_code=409, detail="Lesson is already booked")

    if datetime.fromisoformat(str(lesson.start_time)) < datetime.now():
        raise HTTPException(status_code=400, detail="Lesson in the past cannot be booked")
    
    lesson.assigned_student_id = user.id
    lesson.available = False
 
    db.commit()
    db.refresh(lesson)

    return {
        "lesson_id": lesson.id,
        "start_time": lesson.start_time,
        "end_time": lesson.end_time,
        "duration": lesson.duration,
        "subject": lesson.subject,
        "tutor_id": lesson.tutor_id,
        "assigned_student_id": lesson.assigned_student_id,
        "available": lesson.available,
    }


def update_lesson(token: str, lesson_id: str, update_data, db: Session) -> dict:
    if helpers.is_token_blacklisted(token, db):
        raise HTTPException(status_code=401, detail="Token is invalid")

    decoded_token = helpers.decode_jwt_token(token)
    user = helpers.find_user_info(decoded_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="User does not exist")
    
    lesson = helpers.find_lesson_info(lesson_id, db)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson does not exist")

    if user.role == "student":
        if update_data.start_time or update_data.end_time or update_data.subject:
            raise HTTPException(status_code=403, detail="Only tutors can modify this")

        # TODO: After transferring lessons to be id based instead of email based
        # Make it such that we validate that the student has this tutor as a tutor

        lesson.assigned_student_id = update_data.assigned_student_id
        lesson.available = update_data.available
    elif user.role == "tutor":
        
        if update_data.start_time is not None:
            lesson.start_time = update_data.start_time.isoformat()
        if update_data.end_time is not None:
            lesson.end_time = update_data.end_time.isoformat()
        if update_data.subject is not None:
            lesson.subject = update_data.subject
 
        lesson.assigned_student_id = update_data.assigned_student_id
        lesson.available = update_data.available
 
        helpers.check_lesson_time(user, lesson, lesson_id, db)
    else:
        raise HTTPException(status_code=401, detail="User has invalid role")

    db.commit()
    db.refresh(lesson)
 
    return {
        "lesson_id": lesson.id,
        "start_time": lesson.start_time,
        "end_time": lesson.end_time,
        "duration": lesson.duration,
        "subject": lesson.subject,
        "tutor_id": lesson.tutor_id,
        "assigned_student_id": lesson.assigned_student_id,
        "available": lesson.available,
    }

def delete_lesson(token: str, lesson_id: str, db: Session) -> dict:
    if helpers.is_token_blacklisted(token, db):
        raise HTTPException(status_code=401, detail="Token is invalid")

    decoded_token = helpers.decode_jwt_token(token)
    user = helpers.find_user_info(decoded_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="User does not exist")
    
    lesson = helpers.find_lesson_info(lesson_id, db)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson does not exist")

    if user.role == "student":
        raise HTTPException(status_code=403, detail="Only tutors can modify this")

    if user.id != lesson.tutor_id:
        raise HTTPException(status_code=403, detail="User does not own lesson")
    
    db.delete(lesson)
    db.commit()
 
    return {"message": "lesson deleted successfully"}

