from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
FILE = ROOT / "profit_lab_routes.py"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

backup = ROOT / f"profit_lab_routes.py.bak_rotation_json_v5_{STAMP}"
shutil.copy2(FILE, backup)
print(f"BACKUP | {backup.name}")

txt = FILE.read_text()

old = '"positions": get_positions_safe(),'
new = '"positions": get_positions_safe(),\n        "rotation_engine": build_rotation_engine_v1(s, get_positions_safe()),'

if '"rotation_engine": build_rotation_engine_v1' in txt:
    print("SKIP: rotation_engine already present")
elif old in txt:
    txt = txt.replace(old, new, 1)
    FILE.write_text(txt)
    print("DONE: rotation_engine added to lab JSON")
else:
    print("ERROR: exact positions line not found")
