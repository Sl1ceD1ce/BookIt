from typing import Optional, List
import dataStore as ds

def get_next_user_id() -> str:
    """Generate the next user ID."""
    data = ds.get_data()
    if not data["users"]:
        return "1"
    max_id = max(int(user["id"]) for user in data["users"])
    return str(max_id + 1)

def email_exists(email: str) -> bool:
    """Check if email already exists."""
    data = ds.get_data()
    return any(user["email"] == email for user in data["users"])

def mobile_exists(mobile: str) -> bool:
    """Check if mobile number already exists."""
    data = ds.get_data()
    return any(user["mobile"] == mobile for user in data["users"])

def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email."""
    data = ds.get_data()
    for user in data["users"]:
        if user["email"] == email:
            return user
    return None

def get_user_by_id(user_id: str) -> Optional[dict]:
    """Get user by ID."""
    data = ds.get_data()
    for user in data["users"]:
        if user["id"] == user_id:
            return user
    return None

def get_tutors() -> List[dict]:
    """Get all tutors."""
    data = ds.get_data()
    return [user for user in data["users"] if user["role"] == "tutor"]

def get_students() -> List[dict]:
    """Get all students."""
    data = ds.get_data()
    return [user for user in data["users"] if user["role"] == "student"]

def get_students_for_tutor(tutor_id: str) -> List[dict]:
    """Get all students assigned to a specific tutor."""
    data = ds.get_data()
    return [user for user in data["users"] if user.get("tutor_id") == tutor_id]

def assign_student_to_tutor(student_id: str, tutor_id: str) -> None:
    """Assign a student to a tutor."""
    data = ds.get_data()
    
    student = get_user_by_id(student_id)
    tutor = get_user_by_id(tutor_id)
    
    if not student or student["role"] != "student":
        raise ValueError("Invalid student ID")
    if not tutor or tutor["role"] != "tutor":
        raise ValueError("Invalid tutor ID")
    
    # Update student's tutor_id
    student["tutor_id"] = tutor_id
    
    # Add student to tutor's student_ids list if not already there
    if student_id not in tutor.get("student_ids", []):
        tutor["student_ids"].append(student_id)
    
    ds.save_data()

def add_user(user: dict) -> None:
    """Add a new user to the database."""
    data = ds.get_data()
    data["users"].append(user)
    ds.save_data()

def add_lesson(lesson: dict) -> None:
    """Add a new lesson to the database."""
    data = ds.get_data()
    data["lessons"].append(lesson)
    ds.save_data()