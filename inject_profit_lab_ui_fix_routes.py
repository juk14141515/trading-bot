from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
FILE = ROOT / "profit_lab_routes.py"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

CSS_BLOCK = """
/* PONDER_UI_FIX_ROUTES_V1 */
body{
  overflow-x:hidden!important;
}
.sidebar::after{
  content:"";
  position:absolute;
  left:0;
  top:0;
  bottom:0;
  width:230px;
  background:rgba(5,10,24,.96);
  z-index:-1;
}
.sidebar{
  isolation:isolate;
}
"""

backup = ROOT / f"profit_lab_routes.py.bak_ui_fix_routes_{STAMP}"
shutil.copy2(FILE, backup)
print(f"BACKUP | {backup.name}")

txt = FILE.read_text()

if "PONDER_UI_FIX_ROUTES_V1" in txt:
    print("SKIP: UI fix already installed")
else:
    txt = txt.replace("</style>", CSS_BLOCK + "\n</style>", 1)
    FILE.write_text(txt)
    print("DONE: UI fix injected into profit_lab_routes.py")

print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
