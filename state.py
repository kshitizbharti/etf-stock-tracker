import json
import os
from datetime import datetime

STATE_DIR = "state"

def _state_file():
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(STATE_DIR, f"{today}.json")

def load_state():
    path = _state_file()
    if not os.path.exists(path):
        return {"alerted": {}, "summary_sent": False}
    with open(path, "r") as f:
        return json.load(f)

def save_state(state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(_state_file(), "w") as f:
        json.dump(state, f, indent=2)
