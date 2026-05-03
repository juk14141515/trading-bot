import shutil
from datetime import datetime

FILE = "web_dashboard.py"

# Backup
backup = f"{FILE}.backup_hardpatch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy(FILE, backup)
print(f"Backup created: {backup}")

with open(FILE, "r") as f:
    lines = f.readlines()

new_lines = []
inserted = False

for i, line in enumerate(lines):
    new_lines.append(line)

    # 🔥 THIS IS THE KEY — insert AFTER Open P/L card section
    if 'Open P/L' in line and not inserted:
        new_lines.append("""
        </div>

        <!-- AI SUMMARY BLOCK -->
        <div class="card">
            <h2>AI Market Summary</h2>
            <p>{summary.get("full_summary", "No summary yet.")}</p>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Market Insight</h3>
                <p>{summary.get("market_summary", "N/A")}</p>
            </div>
            <div class="card">
                <h3>Opportunities</h3>
                <p>{summary.get("opportunity_summary", "N/A")}</p>
            </div>
            <div class="card">
                <h3>Risk</h3>
                <p>{summary.get("risk_summary", "N/A")}</p>
            </div>
        </div>
""")
        inserted = True

# Ensure summary variables exist
content = "".join(new_lines)

if "summary = status.get" not in content:
    content = content.replace(
        "logs = read_logs()",
        '''logs = read_logs()
    status = load_bot_status()
    summary = status.get("summary", {})'''
    )

# Ensure loader exists
if "def load_bot_status()" not in content:
    content = content.replace(
        "def read_logs():",
        '''
def load_bot_status():
    try:
        import json
        with open("bot_status.json", "r") as f:
            return json.load(f)
    except:
        return {}

def read_logs():
'''
    )

with open(FILE, "w") as f:
    f.write(content)

print("✅ HARD PATCH COMPLETE")

