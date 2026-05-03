from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_stray_fix_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

# Remove stray floating labels (ONLY raw standalone lines)
bad_lines = [
    "Losing Exposure",
    "Risk Level"
]

lines = txt.split("\n")
cleaned = []
removed = 0

for i, line in enumerate(lines):
    stripped = line.strip()

    # Only remove if it's a standalone label line
    if stripped in bad_lines:
        # Check surrounding lines to avoid deleting legit UI sections
        prev_line = lines[i-1].strip() if i > 0 else ""
        next_line = lines[i+1].strip() if i < len(lines)-1 else ""

        # If it's NOT inside a structured HTML block, remove it
        if "<" not in prev_line and "<" not in next_line:
            removed += 1
            continue

    cleaned.append(line)

p.write_text("\n".join(cleaned))

print(f"DONE: Removed {removed} stray label lines")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
