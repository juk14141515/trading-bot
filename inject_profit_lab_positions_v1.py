from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_profit_lab_positions_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

# Add Alpaca API import from bot.py safely
if "from bot import get_positions" not in txt:
    txt = txt.replace(
        "from profit_ops_analytics import snapshot",
        "from profit_ops_analytics import snapshot\nfrom bot import get_positions"
    )

# Add live positions into lab_snapshot
if '"positions": positions' not in txt:
    txt = txt.replace(
        's["lab"] = {',
        '''positions = []
    try:
        for p in get_positions():
            positions.append({
                "symbol": p.symbol,
                "qty": float(p.qty),
                "entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
                "unrealized_plpc": round(float(p.unrealized_plpc) * 100, 2),
            })
    except Exception as e:
        positions = [{"symbol": "ERROR", "qty": 0, "entry_price": 0, "current_price": 0, "market_value": 0, "unrealized_pl": 0, "unrealized_plpc": 0, "error": str(e)}]

    s["lab"] = {'''
    )

    txt = txt.replace(
        '"win_rate_today": round((wins / len(sells) * 100), 2) if sells else 0,',
        '''"win_rate_today": round((wins / len(sells) * 100), 2) if sells else 0,
        "positions": positions,
        "position_count": len(positions),'''
    )

# Add live position card
if "Live Positions" not in txt:
    txt = txt.replace(
        '<div class="card" style="margin-top:16px">\n    <h2>Trade Replay Table</h2>',
        '''<div class="card" style="margin-top:16px">
    <h2>Live Positions</h2>
    <div class="scroll">
      <table>
        <thead><tr><th>Symbol</th><th>Qty</th><th>Entry</th><th>Current</th><th>Market Value</th><th>Open P/L</th><th>Open P/L %</th></tr></thead>
        <tbody id="positionRows"></tbody>
      </table>
    </div>
  </div>

  <div class="card" style="margin-top:16px">
    <h2>Trade Replay Table</h2>'''
    )

# Add JS render
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

  document.getElementById("feed").textContent=(logs.decision_feed||[]).join("\\\\n") || "No recent decision logs.";'''
    )

p.write_text(txt)

print("DONE: Profit Lab live positions installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
