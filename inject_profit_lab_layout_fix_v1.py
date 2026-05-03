from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_layout_fix_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

# --- 1. Shrink chart height ---
txt = txt.replace("height:400px;", "height:260px;")

# --- 2. Add spacing after chart ---
if "</canvas>" in txt and "height:20px" not in txt:
    txt = txt.replace(
        "</canvas>",
        "</canvas></div><div style='height:20px;'></div>"
    )

# --- 3. Convert sections into grid layout ---
if "Decision Replay" in txt and "grid-template-columns:1fr 1fr 1fr" not in txt:
    txt = txt.replace(
        '<div class="card">\n  <h3>Decision Replay</h3>',
        '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">\n<div class="card">\n  <h3>Decision Replay</h3>'
    )

    txt = txt.replace(
        '</div>\n\n<div class="card">\n  <h3>Live Positions</h3>',
        '</div>\n</div>\n\n<div class="card">\n  <h3>Live Positions</h3>'
    )

# --- 4. Slight styling polish ---
if ".card" in txt and "border-radius:12px" not in txt:
    txt = txt.replace(
        ".card {",
        ".card { border-radius:12px; padding:14px;"
    )

p.write_text(txt)

print("DONE: Profit Lab Layout Fix installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
