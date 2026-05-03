import shutil
import subprocess
from datetime import datetime

FILE = "web_dashboard.py"

backup = f"{FILE}.backup_ai_safe_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy(FILE, backup)
print(f"Backup created: {backup}")

with open(FILE, "r") as f:
    content = f.read()

# Add load_bot_status helper if missing
if "def load_bot_status()" not in content:
    content = content.replace(
        "def read_logs():",
        '''def load_bot_status():
    try:
        import json
        with open("bot_status.json", "r") as f:
            return json.load(f)
    except:
        return {}

def read_logs():'''
    )

# Add status_data inside dashboard()
if "status_data = load_bot_status()" not in content:
    content = content.replace(
        "logs = read_logs()",
        "logs = read_logs()\n    status_data = load_bot_status()"
    )

ai_block = '''
                <div class="card">
                    <h2>AI Market Summary</h2>
                    <p><b>Market:</b> {status_data.get("summary", {}).get("market_summary", "N/A")}</p>
                    <p><b>Opportunities:</b> {status_data.get("summary", {}).get("opportunity_summary", "N/A")}</p>
                    <p><b>Risk:</b> {status_data.get("summary", {}).get("risk_summary", "N/A")}</p>
                    <p>{status_data.get("summary", {}).get("full_summary", "")}</p>
                </div>
'''

# Insert before Open Positions card
if "AI Market Summary" not in content:
    marker = '<div class="card">\n                    <h2>Open Positions</h2>'
    if marker not in content:
        print("ERROR: Could not find Open Positions marker.")
        print("No changes made.")
        shutil.copy(backup, FILE)
        raise SystemExit(1)

    content = content.replace(marker, ai_block + "\n" + marker, 1)

with open(FILE, "w") as f:
    f.write(content)

# Safety compile
result = subprocess.run(["python3", "-m", "py_compile", FILE])

if result.returncode != 0:
    print("Compile failed. Restoring backup.")
    shutil.copy(backup, FILE)
    raise SystemExit(1)

print("AI summary added safely.")
