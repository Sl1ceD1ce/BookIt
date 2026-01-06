import dataStore as ds

def get_next_user_id() -> str:
    data = ds.get_data()
    if not data["users"]:
        return "1"
    max_id = 0
    for user in data["users"]:
        user_id = int(user["id"])
        if user_id > max_id:
            max_id = user_id
    return str(max_id + 1)

def get_next_lesson_id() -> str:
    data = ds.get_data()
    if not data["lessons"]:
        return "1"
    max_id = 0
    for lesson in data["lessons"]:
        lesson_id = int(lesson["id"])
        if lesson_id > max_id:
            max_id = lesson_id
    return str(max_id + 1)

def email_exists(email: str) -> bool:
    data = ds.get_data()
    for user in data["users"]:
        if user["email"] == email:
            return True
    return False

def mobile_exists(mobile: str) -> bool:
    data = ds.get_data()
    for user in data["users"]:
        if user["mobile"] == mobile:
            return True
    return False

def find_user_info(decoded_token: dict) -> str:
    data = ds.get_data()
    for user in data["users"]:
        if decoded_token["user_id"] == user["id"]:
            return user
    return None

def is_token_blacklisted(token: str) -> bool:
    """Check if token has been invalidated"""
    data = ds.get_data()
    for entry in data["invalidated_tokens"]:
        if entry["token"] == token:
            return True
    return False