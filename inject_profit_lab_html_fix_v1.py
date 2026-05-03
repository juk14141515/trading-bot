from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_profit_lab_html_fix_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

# -------------------------
# Fix missing IDs in top cards
# -------------------------
txt = txt.replace(
    'Today P/L</div>\n    <div class="value">$0</div>',
    'Today P/L</div>\n    <div id="todayPnl" class="value">$0</div>\n    <div id="todayStats" class="sub">0 buys · 0 sells</div>'
)

txt = txt.replace(
    'Today Win Rate</div>\n    <div class="value">0%</div>',
    'Today Win Rate</div>\n    <div id="todayWin" class="value">0%</div>\n    <div id="todayWL" class="sub">0 wins · 0 losses</div>'
)

txt = txt.replace(
    'AI Health</div>\n    <div class="value">--</div>',
    'AI Health</div>\n    <div id="health" class="value">--</div>\n    <div id="healthNote" class="sub">Waiting</div>'
)

txt = txt.replace(
    'Open P/L</div>\n    <div class="value">$0</div>',
    'Open P/L</div>\n    <div id="openPl" class="value">$0</div>'
)

# -------------------------
# Fix chart canvas
# -------------------------
if 'id="chart"' not in txt:
    txt = txt.replace(
        'Equity Lab Chart</div>\n  <div style="height:360px">',
        'Equity Lab Chart</div>\n  <div style="height:360px"><canvas id="chart"></canvas>'
    )

# -------------------------
# Add events table ID
# -------------------------
if 'id="events"' not in txt:
    txt = txt.replace(
        'Bot Event Counts</div>',
        'Bot Event Counts</div>\n<table id="events"></table>'
    )

p.write_text(txt)

print("DONE: Profit Lab HTML fixed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
