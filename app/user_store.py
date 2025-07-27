import json
import os

USER_FILE = "data/users.json"

def ensure_file():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)

def load_users():
    ensure_file()
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users: dict):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
