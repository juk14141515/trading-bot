import shutil
from datetime import datetime

FILE = "web_dashboard.py"

backup = f"{FILE}.backup_force_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy(FILE, backup)
print(f"Backup created: {backup}")

with open(FILE, "r") as f:
    content = f.read()

# Ensure status loader exists
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

# Ensure summary variables exist
if "summary = status.get" not in content:
    content = content.replace(
        "logs = read_logs()",
        '''logs = read_logs()
    status = load_bot_status()
    summary = status.get("summary", {})'''
    )

# Add AI block variable
if "ai_summary_html" not in content:
    content = content.replace(
        "rows = \"\"",
        '''rows = ""

    ai_summary_html = f"""
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
    """'''
    )

# FORCE insert before Open Positions
if "{ai_summary_html}" not in content:
    content = content.replace(
        "<h2>Open Positions</h2>",
        """{ai_summary_html}

                <h2>Open Positions</h2>"""
    )

with open(FILE, "w") as f:
    f.write(content)

print("✅ AI Summary FORCE inserted successfully.")
