from pathlib import Path
from datetime import datetime
import shutil
import re

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

file = ROOT / "profit_lab_routes.py"

backup = ROOT / f"profit_lab_routes.py.bak_cleanup_{STAMP}"
shutil.copy2(file, backup)
print(f"BACKUP created: {backup.name}")

txt = file.read_text()

# Remove duplicate Capital Efficiency blocks (keep first one only)
pattern = r'(<div class="card"[^>]*>.*?Capital Efficiency.*?</div>)'
matches = re.findall(pattern, txt, re.DOTALL)

if len(matches) > 1:
    print(f"Found {len(matches)} Capital Efficiency blocks, cleaning...")
    # keep first, remove rest
    for m in matches[1:]:
        txt = txt.replace(m, "")
else:
    print("No duplicates found")

file.write_text(txt)
print("DONE: duplicate panels removed")
