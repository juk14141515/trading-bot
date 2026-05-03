from pathlib import Path
from datetime import datetime
import shutil
import re

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

file = ROOT / "profit_lab_routes.py"

backup = ROOT / f"profit_lab_routes.py.bak_ui_cleanup_{STAMP}"
shutil.copy2(file, backup)
print(f"BACKUP created: {backup.name}")

txt = file.read_text()

# Remove stray label-only lines like "--" or orphaned spans/divs
txt = re.sub(r'>\s*--\s*<', '><', txt)

# Remove duplicated empty grid rows
txt = re.sub(r'<div class="label">.*?</div>\s*<div class="value">--</div>', '', txt)

# Clean extra blank divs
txt = re.sub(r'<div>\s*</div>', '', txt)

file.write_text(txt)

print("DONE: UI artifacts cleaned")
