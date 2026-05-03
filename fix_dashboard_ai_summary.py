import re
import shutil
from datetime import datetime

FILE = "web_dashboard.py"

backup = f"{FILE}.backup_ai_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy(FILE, backup)
print(f"Backup created: {backup}")

with open(FILE, "r") as f:
    content = f.read()

# Add json import if missing
if "import json" not in content:
    content = content.replace("import os\n", "import os\nimport json\n") if "import os\n" in content else "import json\n" + content

# Add load_bot_status() if missing
if "def load_bot_status()" not in content:
    marker = "def read_logs():"
    helper = '''
def load_bot_status():
    try:
        with open("bot_status.json", "r") as f:
            return json.load(f)
    except:
        return {}

'''
    content = content.replace(marker, helper + marker)

# Add status + summary after logs = read_logs()
if "summary = status.get(\"summary\", {})" not in content:
    content = content.replace(
        "logs = read_logs()",
        'logs = read_logs()\n    status = load_bot_status()\n    summary = status.get("summary", {})'
    )

# Add AI summary HTML before return f""" if missing
if "ai_summary_html = f\"\"\"" not in content:
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

# Insert {ai_summary_html} after the first grid closes before Open Positions
if "{ai_summary_html}" not in content:
    content = content.replace(
        '<div class="card">\n                    <h2>Open Positions</h2>',
        '{ai_summary_html}\n\n                <div class="card">\n                    <h2>Open Positions</h2>'
    )

with open(FILE, "w") as f:
    f.write(content)

print("Dashboard AI summary injected successfully.")
