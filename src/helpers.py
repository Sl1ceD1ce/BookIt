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