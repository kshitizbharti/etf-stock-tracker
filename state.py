import json, os
from datetime import date

STATE_DIR = "state"

def today_key():
    return date.today().isoformat()

def load_state():
    os.makedirs(STATE_DIR, exist_ok=True)
    path = f"{STATE_DIR}/{today_key()}.json"
    if not os.path.exists(path):
        return {
            "date": today_key(),
            "alerted": {},
            "summary_sent": False
        }
    with open(path, "r") as f:
        return json.load(f)

def save_state(state):
    path = f"{STATE_DIR}/{today_key()}.json"
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
