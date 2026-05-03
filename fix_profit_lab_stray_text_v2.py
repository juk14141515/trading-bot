from pathlib import Path
from datetime import datetime
import shutil, re

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

p = ROOT / "profit_lab_routes.py"
backup = ROOT / f"profit_lab_routes.py.bak_stray_fix_v2_{STAMP}"
shutil.copy2(p, backup)
print(f"BACKUP | {backup.name}")

txt = p.read_text()

# Remove orphaned Capital Efficiency mini-block fragments that contain only labels/empty values
patterns = [
    r'<div><div class="label">Capital Used</div><div id="capUsed" class="value">--</div></div>',
    r'<div><div class="label">Losing Exposure</div><div id="capLosing" class="value">--</div></div>',
    r'<div><div class="label">Risk Level</div><div id="capRisk" class="value">--</div></div>',
    r'<div class="label">Losing Exposure</div>\s*<div[^>]*>--</div>',
    r'<div class="label">Risk Level</div>\s*<div[^>]*>--</div>',
]

removed = 0
for pat in patterns:
    txt, n = re.subn(pat, "", txt, flags=re.DOTALL)
    removed += n

# Remove any bare text snippets rendered outside cards
txt, n = re.subn(r'\n\s*(Losing Exposure|Risk Level)\s*\n\s*--\s*\n', "\n", txt)
removed += n

p.write_text(txt)
print(f"DONE: removed {removed} fragments")
