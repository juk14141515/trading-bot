from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_learning_shadow_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("bot.py")
backup("profit_lab_routes.py")

# ----------------------------
# 1. Create learning_shadow.py
# ----------------------------
learning = ROOT / "learning_shadow.py"
learning.write_text(r'''
import csv
import json
from pathlib import Path
from datetime import datetime

ROOT = Path("/home/ubuntu/trading-bot")
MEMORY_FILE = ROOT / "learning_shadow_log.csv"
STATE_FILE = ROOT / "learning_shadow_state.json"

FIELDS = [
    "timestamp",
    "event",
    "symbol",
    "score",
    "price",
    "qty",
    "reason",
    "open_pl",
    "rotation_score",
    "rotation_decision",
    "notes"
]

def _ensure_file():
    if not MEMORY_FILE.exists():
        with MEMORY_FILE.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()

def log_learning_event(
    event,
    symbol="-",
    score="",
    price="",
    qty="",
    reason="",
    open_pl="",
    rotation_score="",
    rotation_decision="",
    notes=""
):
    try:
        _ensure_file()
        row = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "symbol": symbol,
            "score": score,
            "price": price,
            "qty": qty,
            "reason": reason,
            "open_pl": open_pl,
            "rotation_score": rotation_score,
            "rotation_decision": rotation_decision,
            "notes": notes
        }
        with MEMORY_FILE.open("a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writerow(row)
        return True
    except Exception:
        return False

def summarize_learning(limit=200):
    _ensure_file()
    rows = []
    try:
        with MEMORY_FILE.open("r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)[-limit:]
    except Exception:
        rows = []

    counts = {}
    symbols = {}

    for r in rows:
        event = r.get("event", "UNKNOWN")
        counts[event] = counts.get(event, 0) + 1

        sym = r.get("symbol") or "-"
        if sym != "-":
            symbols.setdefault(sym, {"events": 0, "buys": 0, "sells": 0})
            symbols[sym]["events"] += 1
            if "BUY" in event:
                symbols[sym]["buys"] += 1
            if "SELL" in event:
                symbols[sym]["sells"] += 1

    return {
        "rows": rows[-50:],
        "counts": counts,
        "symbols": symbols,
        "total": len(rows),
        "mode": "shadow_only"
    }
''')

print("CREATED | learning_shadow.py")

# ----------------------------
# 2. Patch bot.py lightly
# ----------------------------
bot = ROOT / "bot.py"
txt = bot.read_text()

if "from learning_shadow import log_learning_event" not in txt:
    txt = txt.replace(
        "import",
        "from learning_shadow import log_learning_event\nimport",
        1
    )

# Log buy attempts near BUY decision logs
if "LEARNING_SHADOW_BUY_DECISION" not in txt:
    txt = txt.replace(
        'log(f"BUY DECISION | {symbol}',
        'log_learning_event("LEARNING_SHADOW_BUY_DECISION", symbol=symbol, score=final_score, reason="candidate selected")\n            # LEARNING_SHADOW_BUY_DECISION\n            log(f"BUY DECISION | {symbol}'
    )

# Log skipped buys
if "LEARNING_SHADOW_SKIP_BUY" not in txt:
    txt = txt.replace(
        'log(f"SKIP BUY | {symbol}',
        'log_learning_event("LEARNING_SHADOW_SKIP_BUY", symbol=symbol, score=final_score if "final_score" in locals() else "", reason="skip buy")\n            # LEARNING_SHADOW_SKIP_BUY\n            log(f"SKIP BUY | {symbol}'
    )

# Log sells
if "LEARNING_SHADOW_SELL" not in txt:
    txt = txt.replace(
        'log(f"SELL | {symbol}',
        'log_learning_event("LEARNING_SHADOW_SELL", symbol=symbol, qty=qty, reason=reason, open_pl=pnl)\n    # LEARNING_SHADOW_SELL\n    log(f"SELL | {symbol}'
    )

bot.write_text(txt)

# ----------------------------
# 3. Patch profit_lab_routes.py API
# ----------------------------
routes = ROOT / "profit_lab_routes.py"
rtxt = routes.read_text()

if "from learning_shadow import summarize_learning" not in rtxt:
    rtxt = rtxt.replace(
        "from flask import",
        "from learning_shadow import summarize_learning\nfrom flask import",
        1
    )

if '"learning_shadow": summarize_learning()' not in rtxt:
    rtxt = rtxt.replace(
        '"positions": get_positions_safe(),',
        '"positions": get_positions_safe(),\n        "learning_shadow": summarize_learning(),'
    )

# ----------------------------
# 4. Add UI card
# ----------------------------
if "Learning Shadow Mode" not in rtxt:
    rtxt = rtxt.replace(
        '<div class="layout">',
        '''
  <div class="card" style="margin-top:16px">
    <h2>🧪 Learning Shadow Mode</h2>
    <div class="muted">Logs decisions and outcomes only. Does not control trades.</div>
    <div class="grid" style="margin-top:12px">
      <div><div class="label">Mode</div><div class="value good">Shadow</div></div>
      <div><div class="label">Events Logged</div><div id="learnTotal" class="value">--</div></div>
      <div><div class="label">Top Event</div><div id="learnTop" class="value">--</div></div>
      <div><div class="label">Learning Status</div><div id="learnStatus" class="value warn">Collecting</div></div>
    </div>
    <table style="margin-top:12px">
      <thead><tr><th>Time</th><th>Event</th><th>Symbol</th><th>Score</th><th>Reason</th></tr></thead>
      <tbody id="learningRows"></tbody>
    </table>
  </div>

  <div class="layout">'''
    )

# ----------------------------
# 5. Add JS renderer
# ----------------------------
if "learningRows" in rtxt and "lab.learning_shadow" not in rtxt:
    rtxt = rtxt.replace(
        'document.getElementById("positions").innerHTML=(lab.positions||[]).map(p=>`',
        '''const learn=lab.learning_shadow||{};
  if(document.getElementById("learnTotal")){
    const counts=learn.counts||{};
    const top=Object.entries(counts).sort((a,b)=>b[1]-a[1])[0];
    document.getElementById("learnTotal").textContent=learn.total ?? 0;
    document.getElementById("learnTop").textContent=top ? `${top[0]} (${top[1]})` : "--";
    document.getElementById("learnStatus").textContent=(learn.total||0) >= 20 ? "Enough samples soon" : "Collecting";
    document.getElementById("learningRows").innerHTML=(learn.rows||[]).slice(-12).reverse().map(r=>`
      <tr>
        <td>${r.timestamp||""}</td>
        <td>${r.event||""}</td>
        <td>${r.symbol||""}</td>
        <td>${r.score||""}</td>
        <td>${r.reason||""}</td>
      </tr>
    `).join("") || "<tr><td colspan='5'>No learning events yet.</td></tr>";
  }

  document.getElementById("positions").innerHTML=(lab.positions||[]).map(p=>`'''
    )

routes.write_text(rtxt)

print("DONE: Learning Shadow System installed")
print("NEXT:")
print("python3 -m py_compile bot.py profit_lab_routes.py learning_shadow.py")
print("sudo systemctl restart tradebot")
print("sudo systemctl restart tradebot-dashboard")
