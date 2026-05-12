"""Temporary file used to store the data within a file while we learn how to setup the DB."""

import json
import os

DATABASE_FILE = "data.json"

data = {"users": [], "lessons": [], "invalidated_tokens": []}


def get_data():
    """gets data"""
    return data


def load_data():
    """loads data from the file"""
    # pylint: disable=global-statement
    global data
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r", encoding="UTF-8") as f:
            data = json.load(f)


def save_data():
    """saves data to the file"""
    with open(DATABASE_FILE, "w", encoding="UTF-8") as f:
        json.dump(data, f, indent=4)
