from pathlib import Path
import re
from datetime import datetime
import shutil

WEB = Path("web_dashboard.py")

# Backup current broken file
backup = Path(f"web_dashboard_pre_hardfix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
shutil.copy(WEB, backup)

text = WEB.read_text()

# -----------------------------
# 1. REMOVE ANY BROKEN CSS LINES
# -----------------------------
bad_css_patterns = [
    r"\s*padding:\s*\d+px\s*!important;",
    r"\s*font-size:\s*\d+px\s*!important;",
    r"\s*border-radius:\s*\d+px\s*!important;",
]

for pattern in bad_css_patterns:
    text = re.sub(pattern, "", text)

# -----------------------------
# 2. FIX BROKEN RETURN STRINGS
# -----------------------------
text = text.replace('return f"\n<html>', 'return f"""\n<html>')
text = text.replace('</html>"', '</html>"""')

# -----------------------------
# 3. ENSURE MAIN HTML BLOCK IS SAFE
# -----------------------------
if "return f\"\"\"" not in text:
    text = text.replace("return f\"", "return f\"\"\"", 1)

# -----------------------------
# 4. ADD SAFE MOBILE CSS (INSIDE STYLE ONLY)
# -----------------------------
mobile_css = """
@media (max-width: 760px) {
    .container { padding: 12px; }
    .grid, .grid-2 { grid-template-columns: 1fr; }
    .card { padding: 16px; }
    table { display: block; overflow-x: auto; }
}
"""

if mobile_css not in text and "</style>" in text:
    text = text.replace("</style>", mobile_css + "\n</style>", 1)

# -----------------------------
# SAVE
# -----------------------------
WEB.write_text(text)

print("✅ HARD FIX COMPLETE")
print(f"Backup saved: {backup}")
print("Now run:")
print("python3 -m py_compile web_dashboard.py")
print("sudo systemctl restart tradebot-dashboard")
