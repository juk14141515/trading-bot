from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_layout_fix_v2_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

# --- Force clean layout structure ---
if "<!-- LAYOUT_V2 -->" not in txt:
    txt = txt.replace(
        '<canvas id="chart"></canvas>',
        '''<canvas id="chart"></canvas>
</div>

<!-- LAYOUT_V2 -->
<div style="height:20px;"></div>

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;align-items:start">

  <div class="card">
    <h3>Decision Replay</h3>
    <div id="decisionReplay" style="max-height:260px;overflow:auto;font-family:monospace;font-size:13px"></div>
  </div>

  <div class="card">
    <h3>Candidate Feed</h3>
    <table style="width:100%">
      <thead>
        <tr><th>Symbol</th><th>Score</th><th>Reason</th></tr>
      </thead>
      <tbody id="candidateFeed"></tbody>
    </table>
  </div>

  <div class="card">
    <h3>Live Positions</h3>
    <table style="width:100%">
      <thead>
        <tr><th>Symbol</th><th>Qty</th><th>P/L</th></tr>
      </thead>
      <tbody id="positions"></tbody>
    </table>
  </div>

</div>
'''
    )

# --- Ensure chart container is properly sized ---
txt = txt.replace("height:400px;", "height:260px;")

p.write_text(txt)

print("DONE: Clean layout v2 installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
