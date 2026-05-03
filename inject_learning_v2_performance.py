from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_learning_v2_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("learning_shadow.py")
backup("profit_lab_routes.py")

# ----------------------------
# 1. Upgrade learning_shadow.py
# ----------------------------
p = ROOT / "learning_shadow.py"
txt = p.read_text()

if "def summarize_learning_performance" not in txt:
    txt += r'''

def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return 0.0

def summarize_learning_performance(limit=500):
    """
    Learning v2: performance-style summary.
    Shadow-only. Reads learning_shadow_log.csv.
    Does not control trades.
    """
    _ensure_file()

    try:
        with MEMORY_FILE.open("r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)[-limit:]
    except Exception:
        rows = []

    total = len(rows)
    buys = [r for r in rows if "BUY_DECISION" in (r.get("event") or "")]
    skips = [r for r in rows if "SKIP_BUY" in (r.get("event") or "")]
    sells = [r for r in rows if "SELL" in (r.get("event") or "")]

    wins = []
    losses = []
    total_pnl = 0.0

    for r in sells:
        pnl = _safe_float(r.get("open_pl"))
        total_pnl += pnl
        if pnl > 0:
            wins.append(r)
        elif pnl < 0:
            losses.append(r)

    closed = len(sells)
    win_rate = round((len(wins) / closed) * 100, 2) if closed else 0
    avg_win = round(sum(_safe_float(r.get("open_pl")) for r in wins) / len(wins), 2) if wins else 0
    avg_loss = round(sum(_safe_float(r.get("open_pl")) for r in losses) / len(losses), 2) if losses else 0

    symbol_stats = {}
    for r in rows:
        sym = r.get("symbol") or "-"
        if sym == "-":
            continue
        symbol_stats.setdefault(sym, {
            "events": 0,
            "buys": 0,
            "sells": 0,
            "wins": 0,
            "losses": 0,
            "pnl": 0.0
        })

        symbol_stats[sym]["events"] += 1

        event = r.get("event") or ""
        if "BUY_DECISION" in event:
            symbol_stats[sym]["buys"] += 1
        if "SELL" in event:
            pnl = _safe_float(r.get("open_pl"))
            symbol_stats[sym]["sells"] += 1
            symbol_stats[sym]["pnl"] += pnl
            if pnl > 0:
                symbol_stats[sym]["wins"] += 1
            elif pnl < 0:
                symbol_stats[sym]["losses"] += 1

    ranked_symbols = sorted(
        symbol_stats.items(),
        key=lambda x: x[1]["pnl"],
        reverse=True
    )

    best_symbol = ranked_symbols[0][0] if ranked_symbols else "-"
    worst_symbol = ranked_symbols[-1][0] if ranked_symbols else "-"

    status = "Collecting"
    if total >= 20 and closed == 0:
        status = "Decision data ready; waiting for closed trades"
    elif closed >= 5:
        status = "Early performance sample"
    elif closed >= 15:
        status = "Performance sample improving"

    return {
        "mode": "shadow_performance",
        "status": status,
        "total_events": total,
        "buy_decisions": len(buys),
        "skips": len(skips),
        "closed_trades": closed,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": win_rate,
        "total_pnl": round(total_pnl, 2),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "best_symbol": best_symbol,
        "worst_symbol": worst_symbol,
        "symbols": symbol_stats
    }
'''

p.write_text(txt)

# ----------------------------
# 2. Patch profit_lab_routes.py API + UI
# ----------------------------
r = ROOT / "profit_lab_routes.py"
rtxt = r.read_text()

if "summarize_learning_performance" not in rtxt:
    rtxt = rtxt.replace(
        "from learning_shadow import summarize_learning",
        "from learning_shadow import summarize_learning, summarize_learning_performance"
    )

if '"learning_performance": summarize_learning_performance()' not in rtxt:
    rtxt = rtxt.replace(
        '"learning_shadow": summarize_learning(),',
        '"learning_shadow": summarize_learning(),\n        "learning_performance": summarize_learning_performance(),'
    )

if "Learning v2 Performance" not in rtxt:
    rtxt = rtxt.replace(
        '<div class="card" style="margin-top:16px">\n    <h2>🧪 Learning Shadow Mode</h2>',
        '''<div class="card" style="margin-top:16px">
    <h2>📊 Learning v2 Performance</h2>
    <div class="muted">Performance tracking from shadow memory. Read-only.</div>
    <div class="grid" style="margin-top:12px">
      <div><div class="label">Status</div><div id="perfStatus" class="value warn">Collecting</div></div>
      <div><div class="label">Closed Trades</div><div id="perfClosed" class="value">0</div></div>
      <div><div class="label">Win Rate</div><div id="perfWinRate" class="value">0%</div></div>
      <div><div class="label">Shadow P/L</div><div id="perfPnl" class="value">$0.00</div></div>
    </div>
    <div class="grid" style="margin-top:12px">
      <div><div class="label">Buy Decisions</div><div id="perfBuys" class="value">0</div></div>
      <div><div class="label">Skips</div><div id="perfSkips" class="value">0</div></div>
      <div><div class="label">Best Symbol</div><div id="perfBest" class="value">-</div></div>
      <div><div class="label">Worst Symbol</div><div id="perfWorst" class="value">-</div></div>
    </div>
  </div>

  <div class="card" style="margin-top:16px">
    <h2>🧪 Learning Shadow Mode</h2>'''
    )

if "lab.learning_performance" not in rtxt:
    rtxt = rtxt.replace(
        'const learn=lab.learning_shadow||{};',
        '''const perf=lab.learning_performance||{};
  if(document.getElementById("perfStatus")){
    document.getElementById("perfStatus").textContent=perf.status||"Collecting";
    document.getElementById("perfClosed").textContent=perf.closed_trades ?? 0;
    document.getElementById("perfWinRate").textContent=(perf.win_rate ?? 0)+"%";
    document.getElementById("perfPnl").textContent=money(perf.total_pnl||0);
    document.getElementById("perfPnl").className="value "+cls(perf.total_pnl||0);
    document.getElementById("perfBuys").textContent=perf.buy_decisions ?? 0;
    document.getElementById("perfSkips").textContent=perf.skips ?? 0;
    document.getElementById("perfBest").textContent=perf.best_symbol||"-";
    document.getElementById("perfWorst").textContent=perf.worst_symbol||"-";
  }

  const learn=lab.learning_shadow||{};'''
    )

r.write_text(rtxt)

print("DONE: Learning v2 performance tracking installed")
print("NEXT:")
print("python3 -m py_compile learning_shadow.py profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
