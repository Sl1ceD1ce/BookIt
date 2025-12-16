import json
import os

DATABASE_FILE = "data.json"

data = {"users": [], "lessons": []}


def get_data():
    return data


def load_data():
    global data
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r") as f:
            data = json.load(f)


def save_data():
    with open(DATABASE_FILE, "w") as f:
        json.dump(data, f, indent=4)
