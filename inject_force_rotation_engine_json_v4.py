from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
FILE = ROOT / "profit_lab_routes.py"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

backup = ROOT / f"profit_lab_routes.py.bak_force_rotation_json_v4_{STAMP}"
shutil.copy2(FILE, backup)
print(f"BACKUP | {backup.name}")

txt = FILE.read_text()

needle = '"positions": positions,'
insert = '"positions": positions,\n        "rotation_engine": build_rotation_engine_v1(s, positions),'

if insert in txt:
    print("SKIP: rotation_engine already in lab JSON")
elif needle in txt:
    txt = txt.replace(needle, insert, 1)
    print("DONE: inserted rotation_engine after positions")
else:
    print("ERROR: could not find positions line")
    print("Run: grep -n 'positions' profit_lab_routes.py | head -20")

FILE.write_text(txt)
