import json
from datetime import datetime

STATUS_FILE = "bot_status.json"

def update_status(data):
    data["last_updated"] = datetime.utcnow().isoformat()
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_status():
    try:
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}
