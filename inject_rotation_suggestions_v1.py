from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_rotation_suggestions_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

# ----------------------------
# Backend helper
# ----------------------------
if "def build_rotation_suggestions" not in txt:
    txt = txt.replace(
        "def lab_snapshot():",
        r'''
def build_rotation_suggestions(positions):
    suggestions = []
    if not positions:
        return [{
            "action": "WAIT",
            "symbol": "-",
            "reason": "No open positions to rotate.",
            "severity": "info"
        }]

    ranked = sorted(
        positions,
        key=lambda p: (
            float(p.get("unrealized_plpc", 0)),
            float(p.get("unrealized_pl", 0))
        )
    )

    weakest = ranked[0]
    pnl_pct = float(weakest.get("unrealized_plpc", 0))
    pnl = float(weakest.get("unrealized_pl", 0))
    symbol = weakest.get("symbol", "-")

    if pnl_pct <= -4:
        suggestions.append({
            "action": "WATCH CLOSELY",
            "symbol": symbol,
            "reason": f"Weakest position is down {pnl_pct:.2f}% / ${pnl:.2f}. Candidate for future rotation or guard review.",
            "severity": "bad"
        })
    elif pnl_pct <= -2:
        suggestions.append({
            "action": "MONITOR",
            "symbol": symbol,
            "reason": f"Position is meaningfully negative at {pnl_pct:.2f}%. Do not rotate automatically yet; collect more closed-trade data.",
            "severity": "warn"
        })
    else:
        suggestions.append({
            "action": "HOLD",
            "symbol": symbol,
            "reason": f"Weakest position is only {pnl_pct:.2f}%. No rotation pressure right now.",
            "severity": "good"
        })

    winners = [p for p in positions if float(p.get("unrealized_pl", 0)) > 0]
    losers = [p for p in positions if float(p.get("unrealized_pl", 0)) < 0]

    suggestions.append({
        "action": "POSITION MIX",
        "symbol": "ALL",
        "reason": f"{len(winners)} winners / {len(losers)} losers. Rotation should stay suggestion-only until 15–20 closed trades.",
        "severity": "info"
    })

    return suggestions


def lab_snapshot():'''
    )

# Add to lab JSON
if '"rotation_suggestions": build_rotation_suggestions' not in txt:
    txt = txt.replace(
        '"candidate_feed": build_candidates(logs),',
        '"candidate_feed": build_candidates(logs),\n        "rotation_suggestions": build_rotation_suggestions(get_positions_safe()),'
    )

# ----------------------------
# UI section
# ----------------------------
if "Rotation Suggestions" not in txt:
    txt = txt.replace(
        '<div class="layout">',
        '''
  <div class="card" style="margin-top:16px">
    <h2>🔁 Rotation Suggestions</h2>
    <div class="muted">Suggestion-only mode. No trades are executed from this panel.</div>
    <table style="margin-top:12px">
      <thead><tr><th>Action</th><th>Symbol</th><th>Reason</th></tr></thead>
      <tbody id="rotationSuggestions"></tbody>
    </table>
  </div>

  <div class="layout">'''
    )

# ----------------------------
# JS renderer
# ----------------------------
if "rotationSuggestions" in txt and "lab.rotation_suggestions" not in txt:
    txt = txt.replace(
        'document.getElementById("positions").innerHTML=(lab.positions||[]).map(p=>`',
        '''const rotEl=document.getElementById("rotationSuggestions");
  if(rotEl){
    rotEl.innerHTML=(lab.rotation_suggestions||[]).map(x=>`
      <tr>
        <td class="${x.severity||'info'}">${x.action||''}</td>
        <td>${x.symbol||''}</td>
        <td>${x.reason||''}</td>
      </tr>
    `).join("") || "<tr><td colspan='3'>No rotation suggestions yet.</td></tr>";
  }

  document.getElementById("positions").innerHTML=(lab.positions||[]).map(p=>`'''
    )

p.write_text(txt)

print("DONE: Rotation Suggestions V1 installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
