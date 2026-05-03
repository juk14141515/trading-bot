from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_clean_v3_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

# REMOVE any previous injections completely
start = txt.find("<canvas id=\"chart\">")
end = txt.find("</script>")

if start != -1 and end != -1:
    before = txt[:start]
    after = txt[end:]

    new_block = '''
<canvas id="chart"></canvas>
</div>

<div style="height:20px;"></div>

<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px">

  <div class="card">
    <h3>Decision Replay</h3>
    <pre id="decisionReplay"></pre>
  </div>

  <div class="card">
    <h3>Candidate Feed</h3>
    <table>
      <thead>
        <tr><th>Symbol</th><th>Score</th><th>Reason</th></tr>
      </thead>
      <tbody id="candidateFeed"></tbody>
    </table>
  </div>

  <div class="card">
    <h3>Live Positions</h3>
    <table>
      <thead>
        <tr><th>Symbol</th><th>Qty</th><th>P/L</th></tr>
      </thead>
      <tbody id="positions"></tbody>
    </table>
  </div>

</div>
'''

    txt = before + new_block + after

p.write_text(txt)

print("DONE: Clean Profit Lab UI rebuilt")
