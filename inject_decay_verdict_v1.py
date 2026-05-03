from pathlib import Path
from datetime import datetime, timezone
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_decay_verdict_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

# Add json/time imports
if "import json" not in txt:
    txt = txt.replace("import os", "import os\nimport json\nimport time")

# Add persistent losing timer helper
if "def enrich_position_timers" not in txt:
    txt = txt.replace(
        "def build_replay(logs):",
        r'''
POSITION_TIMER_FILE = "/home/ubuntu/trading-bot/position_timers.json"

def _fmt_duration(seconds):
    seconds = int(max(0, seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if h:
        return f"{h}h {m}m"
    return f"{m}m"

def enrich_position_timers(positions):
    now = time.time()
    try:
        with open(POSITION_TIMER_FILE, "r") as f:
            timers = json.load(f)
    except Exception:
        timers = {}

    active = set()
    changed = False

    for pos in positions:
        symbol = pos.get("symbol", "-")
        active.add(symbol)

        pnl = float(pos.get("unrealized_pl", 0) or 0)
        rec = timers.get(symbol, {})

        if "first_seen" not in rec:
            rec["first_seen"] = now
            changed = True

        if pnl < 0:
            if "losing_since" not in rec or not rec.get("losing_since"):
                rec["losing_since"] = now
                changed = True
        else:
            if rec.get("losing_since"):
                rec["losing_since"] = None
                changed = True

        timers[symbol] = rec

        held_seconds = now - float(rec.get("first_seen", now))
        losing_since = rec.get("losing_since")
        losing_seconds = now - float(losing_since) if losing_since else 0

        pos["held_for"] = _fmt_duration(held_seconds)
        pos["held_seconds"] = int(held_seconds)
        pos["held_losing_for"] = _fmt_duration(losing_seconds) if losing_seconds else "not losing"
        pos["held_losing_seconds"] = int(losing_seconds)

    for symbol in list(timers.keys()):
        if symbol not in active:
            timers.pop(symbol, None)
            changed = True

    if changed:
        try:
            with open(POSITION_TIMER_FILE, "w") as f:
                json.dump(timers, f)
        except Exception:
            pass

    return positions

def build_replay(logs):'''
    )

# Ensure positions get timers
txt = txt.replace(
    '"positions": get_positions_safe(),',
    '"positions": enrich_position_timers(get_positions_safe()),'
)

# Upgrade rotation suggestions to use real timer if present
if "timer_points" not in txt:
    txt = txt.replace(
        "confidence = int(min(95, severity_points + exposure_points + drag_points))",
        '''timer_points = min(15, float(weakest.get("held_losing_seconds", 0) or 0) / 3600 * 5)
    confidence = int(min(95, severity_points + exposure_points + drag_points + timer_points))'''
    )

    txt = txt.replace(
        '"held_losing_for": "collecting",',
        '"held_losing_for": weakest.get("held_losing_for", "collecting"),'
    )

# Add verdict builder
if "def build_ponder_verdict" not in txt:
    txt = txt.replace(
        "def lab_snapshot():",
        r'''
def build_ponder_verdict(s, positions):
    health = float((s.get("health") or {}).get("score") or 0)
    latest = s.get("latest") or {}
    open_pl = float(latest.get("open_pl") or 0)
    closed = int((s.get("metrics") or {}).get("closed_trades") or 0)

    verdict = {
        "status": "MONITOR",
        "tone": "warn",
        "summary": "System is collecting data. Keep automation conservative.",
        "bullets": [],
        "next_action": "Wait for more closed trades before enabling automation."
    }

    if positions:
        weakest = sorted(positions, key=lambda p: float(p.get("unrealized_pl", 0) or 0))[0]
        verdict["bullets"].append(
            f"Weakest position: {weakest.get('symbol')} at ${float(weakest.get('unrealized_pl',0)):.2f} / {float(weakest.get('unrealized_plpc',0)):.2f}%."
        )
        verdict["bullets"].append(
            f"Losing timer: {weakest.get('held_losing_for', 'collecting')}."
        )

        if float(weakest.get("unrealized_plpc", 0) or 0) <= -4:
            verdict["status"] = "WATCH CLOSELY"
            verdict["tone"] = "bad"
            verdict["summary"] = "One position is creating meaningful drag."
            verdict["next_action"] = "Do not auto-rotate yet; monitor guard/exit behavior."

    if open_pl < 0:
        verdict["bullets"].append(f"Open P/L is negative at ${open_pl:.2f}.")
    else:
        verdict["bullets"].append(f"Open P/L is stable at ${open_pl:.2f}.")

    if health >= 80:
        verdict["bullets"].append("AI health is strong, but closed-trade data is still limited.")
    elif health >= 70:
        verdict["bullets"].append("AI health is acceptable; defensive monitoring is appropriate.")
    else:
        verdict["bullets"].append("AI health is weak; avoid adding automation.")

    if closed < 15:
        verdict["bullets"].append(f"Only {closed} closed trades. Rotation automation is NOT READY.")
    else:
        verdict["status"] = "READY TO REVIEW"
        verdict["tone"] = "good"
        verdict["next_action"] = "Enough closed trades to start reviewing controlled automation."

    return verdict

def lab_snapshot():'''
    )

# Modify lab_snapshot to store positions once, then reuse
txt = txt.replace(
    '''s["lab"] = {
        "today": today,''',
    '''positions = enrich_position_timers(get_positions_safe())

    s["lab"] = {
        "today": today,'''
)

txt = txt.replace(
    '"positions": enrich_position_timers(get_positions_safe()),',
    '"positions": positions,'
)

if '"ponder_verdict": build_ponder_verdict' not in txt:
    txt = txt.replace(
        '"rotation_suggestions": build_rotation_suggestions(get_positions_safe()),',
        '"rotation_suggestions": build_rotation_suggestions(positions),\n        "ponder_verdict": build_ponder_verdict(s, positions),'
    )

# Add Verdict UI
if "Ponder Verdict" not in txt:
    txt = txt.replace(
        '<div class="card">\n    <h2>⚡ Quick Status</h2>',
        '''<div class="card">
    <h2>🐾 Ponder Verdict</h2>
    <div id="verdictStatus" class="value warn">MONITOR</div>
    <div id="verdictSummary" class="muted" style="margin-top:8px">Loading verdict...</div>
    <ul id="verdictBullets" style="line-height:1.7;margin-top:10px"></ul>
    <div class="label">Next Action</div>
    <div id="verdictNext" class="info" style="font-weight:800;margin-top:6px">Waiting...</div>
  </div>

  <div class="card">
    <h2>⚡ Quick Status</h2>'''
    )

# Add columns to positions table
txt = txt.replace(
    '<thead><tr><th>Symbol</th><th>Qty</th><th>Open P/L</th><th>P/L %</th></tr></thead>',
    '<thead><tr><th>Symbol</th><th>Qty</th><th>Open P/L</th><th>P/L %</th><th>Held</th><th>Losing For</th></tr></thead>'
)

txt = txt.replace(
    '''<td class="${cls(p.unrealized_plpc)}">${pct(p.unrealized_plpc)}</td>
    </tr>''',
    '''<td class="${cls(p.unrealized_plpc)}">${pct(p.unrealized_plpc)}</td>
      <td>${p.held_for||"collecting"}</td>
      <td>${p.held_losing_for||"not losing"}</td>
    </tr>'''
)

txt = txt.replace(
    '"<tr><td colspan=\'4\'>No open positions.</td></tr>"',
    '"<tr><td colspan=\'6\'>No open positions.</td></tr>"'
)

# Add JS verdict renderer
if "verdictStatus" in txt and "lab.ponder_verdict" not in txt:
    txt = txt.replace(
        'document.getElementById("decisionReplay").innerHTML=(lab.decision_replay||[]).map(x=>`',
        '''const verdict=lab.ponder_verdict||{};
  const verdictStatus=document.getElementById("verdictStatus");
  if(verdictStatus){
    verdictStatus.textContent=verdict.status||"MONITOR";
    verdictStatus.className="value "+(verdict.tone||"warn");
    document.getElementById("verdictSummary").textContent=verdict.summary||"";
    document.getElementById("verdictBullets").innerHTML=(verdict.bullets||[]).map(x=>`<li>${x}</li>`).join("");
    document.getElementById("verdictNext").textContent=verdict.next_action||"Keep monitoring.";
  }

  document.getElementById("decisionReplay").innerHTML=(lab.decision_replay||[]).map(x=>`'''
    )

p.write_text(txt)

print("DONE: Real decay timer + Ponder Verdict installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
