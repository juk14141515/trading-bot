from pathlib import Path
from datetime import datetime
import shutil
import re

WEB = Path("web_dashboard.py")

# Backup current file
backup = Path(f"web_dashboard_nuclear_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
shutil.copy(WEB, backup)

text = WEB.read_text()

# -----------------------------
# 1. REMOVE ALL RAW CSS LINES OUTSIDE STRINGS
# -----------------------------
lines = text.splitlines()
cleaned = []

for line in lines:
    # if line looks like CSS and is NOT inside a string → remove it
    if any(x in line for x in [
        "px;",
        "blur(",
        "backdrop-filter",
        "font-size:",
        "padding:",
        "border-radius:",
        "grid-template",
    ]):
        if '"""' not in line and "'" not in line:
            continue
    cleaned.append(line)

text = "\n".join(cleaned)

# -----------------------------
# 2. FORCE CORRECT HTML RETURN BLOCK
# -----------------------------
text = re.sub(
    r"return f\".*?<html>",
    'return f"""\n<html>',
    text,
    count=1,
    flags=re.DOTALL
)

text = re.sub(
    r"</html>\"",
    '</html>"""',
    text
)

# -----------------------------
# 3. ENSURE STYLE BLOCK EXISTS
# -----------------------------
if "<style>" not in text:
    text = text.replace(
        "<head>",
        """<head>
        <style>
        body { background:#030712; color:white; font-family:Arial; }
        .card { background:#0f172a; padding:16px; border-radius:16px; }
        </style>
        """
    )

# -----------------------------
# 4. ADD SAFE MOBILE CSS (INSIDE STYLE ONLY)
# -----------------------------
mobile_css = """
@media (max-width: 760px) {
    .container { padding: 12px; }
    .grid, .grid-2 { grid-template-columns: 1fr; }
    .card { padding: 14px; }
    table { display:block; overflow-x:auto; }
}
"""

if "</style>" in text and mobile_css not in text:
    text = text.replace("</style>", mobile_css + "\n</style>", 1)

# -----------------------------
# SAVE
# -----------------------------
WEB.write_text(text)

print("🔥 NUCLEAR FIX COMPLETE")
print(f"Backup saved: {backup}")
print("Run next:")
print("python3 -m py_compile web_dashboard.py")
print("sudo systemctl restart tradebot-dashboard")
