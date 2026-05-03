from pathlib import Path
import re

files = [
    "web_dashboard.py",
    "profit_ops_routes.py",
    "profit_lab_routes.py"
]

patterns = [
    r"AI Health:.*?</div>",
    r"<div[^>]*AI Health[^>]*>.*?</div>",
    r"position:\s*fixed[^;]*;[^}]*AI Health[^}]*}",
]

for file in files:
    p = Path(file)
    if not p.exists():
        continue

    text = p.read_text()

    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.DOTALL)

    p.write_text(text)
    print(f"✅ Cleaned floating AI Health from {file}")

print("DONE")
