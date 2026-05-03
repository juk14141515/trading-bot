from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_profit_lab_live_v2_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")
backup("profit_ops_routes.py")

# -------------------------
# Patch Profit Lab safely
# -------------------------
p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

if "import os" not in txt:
    txt = "import os\n" + txt

if "import alpaca_trade_api as tradeapi" not in txt:
    txt = txt.replace(
        "import os\n",
        "import os\nimport alpaca_trade_api as tradeapi\n"
    )

if "def get_live_positions_safe" not in txt:
    txt = txt.replace(
        "def lab_snapshot():",
        r'''
def get_live_positions_safe():
    try:
        key = os.getenv("APCA_API_KEY_ID")
        secret = os.getenv("APCA_API_SECRET_KEY")
        base_url = os.getenv("BASE_URL") or os.getenv("APCA_API_BASE_URL") or "https://paper-api.alpaca.markets"

        if not key or not secret:
            return []

        api = tradeapi.REST(key, secret, base_url, api_version="v2")
        rows = []

        for p in api.list_positions():
            rows.append({
                "symbol": p.symbol,
                "qty": float(p.qty),
                "entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": round(float(p.unrealized_plpc) * 100, 2),
            })

        return rows
    except Exception as e:
        return [{
            "symbol": "ERROR",
            "qty": 0,
            "entry_price": 0,
            "current_price": 0,
            "market_value": 0,
            "unrealized_pl": 0,
            "unrealized_plpc": 0,
            "error": str(e)
        }]

def pseudo_replay_from_logs(s):
    rows = []
    for line in s.get("recent_logs", [])[-80:]:
        if any(k in line for k in ["P/L |", "SKIP BUY", "BUY DECISION", "CONFIDENCE", "ROTATION", "SELL", "TRADE GUARD"]):
            rows.append(line)
    return rows[-60:]

def lab_snapshot():'''
    )

if '"positions": get_live_positions_safe()' not in txt:
    txt = txt.replace(
        '"win_rate_today": round((wins / len(sells) * 100), 2) if sells else 0,',
        '''"win_rate_today": round((wins / len(sells) * 100), 2) if sells else 0,
        "positions": get_live_positions_safe(),
        "pseudo_replay": pseudo_replay_from_logs(s),'''
    )

if "Live Open Positions" not in txt:
    txt = txt.replace(
        '<div class="card" style="margin-top:16px">\n    <h2>Trade Replay Table</h2>',
        '''<div class="card" style="margin-top:16px">
    <h2>Live Open Positions</h2>
    <div class="scroll">
      <table>
        <thead><tr><th>Symbol</th><th>Qty</th><th>Entry</th><th>Current</th><th>Market Value</th><th>Open P/L</th><th>Open P/L %</th></tr></thead>
        <tbody id="positionRows"></tbody>
      </table>
    </div>
  </div>

  <div class="card" style="margin-top:16px">
    <h2>Pseudo Replay From Logs</h2>
    <pre id="pseudoReplay"></pre>
  </div>

  <div class="card" style="margin-top:16px">
    <h2>Trade Replay Table</h2>'''
    )

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

# -------------------------
# Add Profit Lab link to Profit Ops nav
# -------------------------
ops = ROOT / "profit_ops_routes.py"
otxt = ops.read_text()

if "Profit Lab" not in otxt:
    otxt = otxt.replace(
        '<a href="/">Main Dashboard</a> · <a href="/profit">Profit Ops</a> · <a href="/history">History</a> · <a href="/logout">Logout</a>',
        '<a href="/">Main Dashboard</a> · <a href="/profit">Profit Ops</a> · <a href="/profit-lab">Profit Lab</a> · <a href="/history">History</a> · <a href="/logout">Logout</a>'
    )

ops.write_text(otxt)

print("DONE: Profit Lab Live V2 installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py profit_ops_routes.py")
print("sudo systemctl restart tradebot-dashboard")
