from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_profit_lab_render_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

# Add Live Positions + Pseudo Replay sections if missing
if "Live Open Positions" not in txt:
    txt = txt.replace(
        '<div class="card" style="margin-top:16px">\n    <h2>Trade Replay Table</h2>',
        '''<div class="card" style="margin-top:16px">
    <h2>Live Open Positions</h2>
    <div class="scroll">
      <table>
        <thead>
          <tr>
            <th>Symbol</th><th>Qty</th><th>Entry</th><th>Current</th>
            <th>Market Value</th><th>Open P/L</th><th>Open P/L %</th>
          </tr>
        </thead>
        <tbody id="positionRows"></tbody>
      </table>
    </div>
  </div>

  <div class="card" style="margin-top:16px">
    <h2>Bot Pseudo Replay</h2>
    <pre id="pseudoReplay"></pre>
  </div>

  <div class="card" style="margin-top:16px">
    <h2>Trade Replay Table</h2>'''
    )

# Add JS rendering if missing
if "positionRows" in txt and "lab.positions" not in txt:
    txt = txt.replace(
        'document.getElementById("feed").textContent=(logs.decision_feed||[]).join("\\\\n") || "No recent decision logs.";',

        '''if(document.getElementById("positionRows")){
    document.getElementById("positionRows").innerHTML=(lab.positions||[]).map(p=>`<tr>
      <td>${p.symbol||""}</td>
      <td>${p.qty||""}</td>
      <td>${money(p.entry_price)}</td>
      <td>${money(p.current_price)}</td>
      <td>${money(p.market_value)}</td>
      <td class="${cls(p.unrealized_pl)}">${money(p.unrealized_pl)}</td>
      <td class="${cls(p.unrealized_plpc)}">${pct(p.unrealized_plpc)}</td>
    </tr>`).join("") || "<tr><td colspan='7'>No open positions.</td></tr>";
  }

  if(document.getElementById("pseudoReplay")){
    document.getElementById("pseudoReplay").textContent=(lab.pseudo_replay||[]).join("\\n") || "No replay-style logs yet.";
  }

  document.getElementById("feed").textContent=(logs.decision_feed||[]).join("\\\\n") || "No recent decision logs.";'''
    )

p.write_text(txt)

print("DONE: Profit Lab render patch installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
