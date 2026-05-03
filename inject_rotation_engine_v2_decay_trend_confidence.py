from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
FILE = ROOT / "profit_lab_routes.py"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

backup = ROOT / f"profit_lab_routes.py.bak_rotation_v2_decay_{STAMP}"
shutil.copy2(FILE, backup)
print(f"BACKUP | {backup.name}")

txt = FILE.read_text()

start = txt.find("def build_rotation_engine_v1")
end = txt.find("\ndef lab_snapshot():", start)

engine = r'''
ROTATION_STATE_FILE = "/home/ubuntu/trading-bot/rotation_engine_state.json"

def build_rotation_engine_v1(s, positions):
    import json, time, os

    metrics = s.get("metrics") or {}
    latest = s.get("latest") or {}
    closed = int(metrics.get("closed_trades") or 0)
    win_rate = float(metrics.get("win_rate") or 0)
    open_pl = float(latest.get("open_pl") or 0)
    positions = positions or []

    def pl(p):
        return float(p.get("unrealized_pl") or p.get("open_pl") or p.get("pnl") or 0)

    def plpc(p):
        return float(p.get("unrealized_plpc") or p.get("pl_pct") or p.get("pnl_pct") or 0)

    try:
        with open(ROTATION_STATE_FILE, "r") as f:
            state_cache = json.load(f)
    except Exception:
        state_cache = {}

    now = time.time()

    if not positions:
        return {
            "score": 0,
            "score_trend": "flat",
            "confidence": 0,
            "state": "IDLE",
            "pressure": "LOW",
            "readiness": "NOT READY",
            "readiness_score": min(100, int((closed / 20) * 100)),
            "decision": "WAIT",
            "weakest": "-",
            "weakest_pnl": 0,
            "weakest_pnl_pct": 0,
            "best_offset": "-",
            "best_offset_pnl": 0,
            "best_offset_pnl_pct": 0,
            "decay": "none",
            "suggested_move": "No open positions to evaluate.",
            "reason": "Rotation engine is observing only."
        }

    weakest = sorted(positions, key=lambda p: plpc(p))[0]
    strongest = sorted(positions, key=lambda p: plpc(p))[-1]

    weakest_symbol = weakest.get("symbol", "-")
    weakest_pl = pl(weakest)
    weakest_pct = plpc(weakest)

    losers = [p for p in positions if pl(p) < 0]
    winners = [p for p in positions if pl(p) > 0]

    rec = state_cache.get(weakest_symbol, {})
    prev_score = float(rec.get("last_score", 0))
    prev_pl = float(rec.get("last_pl", weakest_pl))
    losing_since = rec.get("losing_since")

    if weakest_pl < 0:
        if not losing_since:
            losing_since = now
    else:
        losing_since = None

    losing_seconds = now - losing_since if losing_since else 0

    severity = min(40, abs(min(weakest_pct, 0)) * 8)
    dollar_drag = min(25, abs(min(weakest_pl, 0)) / 35)
    portfolio_drag = min(15, abs(min(open_pl, 0)) / 40)
    mix_drag = 10 if len(losers) > len(winners) else 0
    decay_drag = min(10, losing_seconds / 3600 * 4)

    score = int(min(100, severity + dollar_drag + portfolio_drag + mix_drag + decay_drag))

    if score > prev_score + 3:
        score_trend = "rising"
    elif score < prev_score - 3:
        score_trend = "cooling"
    else:
        score_trend = "flat"

    if weakest_pl < prev_pl - 10:
        decay = "worsening"
    elif weakest_pl > prev_pl + 10:
        decay = "improving"
    elif weakest_pl < 0:
        decay = "stale loss"
    else:
        decay = "healthy"

    readiness_score = min(100, int((closed / 20) * 80 + (win_rate / 100) * 20))
    readiness = "READY TO REVIEW" if closed >= 15 else "NOT READY"

    confidence = int(min(95, score * 0.65 + readiness_score * 0.25 + (10 if score_trend == "rising" else 0)))

    if score >= 75:
        engine_state = "ROTATION PRESSURE"
        pressure = "HIGH"
    elif score >= 50:
        engine_state = "WATCH"
        pressure = "MEDIUM"
    else:
        engine_state = "HOLD"
        pressure = "LOW"

    if readiness != "READY TO REVIEW":
        decision = "DO NOT ROTATE"
        suggested = "Suggestion-only. Need 15–20 closed trades before automation."
    elif score >= 75 and confidence >= 70:
        decision = "REVIEW ROTATION"
        suggested = "Rotation pressure is high. Review manually before execution."
    elif score >= 50:
        decision = "WATCH"
        suggested = "Monitor weakest position. Pressure is building."
    else:
        decision = "HOLD"
        suggested = "Rotation pressure is low."

    state_cache[weakest_symbol] = {
        "last_score": score,
        "last_pl": weakest_pl,
        "last_seen": now,
        "losing_since": losing_since
    }

    try:
        with open(ROTATION_STATE_FILE, "w") as f:
            json.dump(state_cache, f)
    except Exception:
        pass

    def fmt_time(sec):
        sec = int(max(0, sec))
        h = sec // 3600
        m = (sec % 3600) // 60
        return f"{h}h {m}m" if h else f"{m}m"

    return {
        "score": score,
        "score_trend": score_trend,
        "confidence": confidence,
        "state": engine_state,
        "pressure": pressure,
        "readiness": readiness,
        "readiness_score": readiness_score,
        "decision": decision,
        "weakest": weakest_symbol,
        "weakest_pnl": round(weakest_pl, 2),
        "weakest_pnl_pct": round(weakest_pct, 2),
        "best_offset": strongest.get("symbol", "-"),
        "best_offset_pnl": round(pl(strongest), 2),
        "best_offset_pnl_pct": round(plpc(strongest), 2),
        "decay": decay,
        "losing_for": fmt_time(losing_seconds),
        "suggested_move": suggested,
        "reason": f"{weakest_symbol} is weakest at {weakest_pct:.2f}% / ${weakest_pl:.2f}. {len(winners)} winners / {len(losers)} losers. Pressure trend is {score_trend}; decay is {decay}."
    }

'''

if start != -1 and end != -1:
    txt = txt[:start] + engine + txt[end:]
else:
    txt = txt.replace("def lab_snapshot():", engine + "\ndef lab_snapshot():")

# Upgrade UI labels if present
txt = txt.replace(
    '<div><div class="label">Readiness</div><div id="rotReadiness" class="value">--</div></div>',
    '''<div><div class="label">Readiness</div><div id="rotReadiness" class="value">--</div></div>
      <div><div class="label">Confidence</div><div id="rotConfidence" class="value">--</div></div>
      <div><div class="label">Trend</div><div id="rotTrend" class="value">--</div></div>
      <div><div class="label">Decay</div><div id="rotDecay" class="value">--</div></div>'''
)

# Upgrade JS renderer
txt = txt.replace(
    'document.getElementById("rotReadiness").textContent=engine.readiness||"--";',
    '''document.getElementById("rotReadiness").textContent=(engine.readiness||"--") + " (" + (engine.readiness_score ?? 0) + "/100)";
    if(document.getElementById("rotConfidence")) document.getElementById("rotConfidence").textContent=(engine.confidence ?? 0) + "%";
    if(document.getElementById("rotTrend")) document.getElementById("rotTrend").textContent=engine.score_trend||"--";
    if(document.getElementById("rotDecay")) document.getElementById("rotDecay").textContent=(engine.decay||"--") + " · " + (engine.losing_for||"0m");'''
)

# Upgrade details with reason
txt = txt.replace(
    'document.getElementById("rotMove").textContent=engine.suggested_move||"Keep monitoring.";',
    '''document.getElementById("rotMove").textContent=(engine.suggested_move||"Keep monitoring.") + " " + (engine.reason||"");'''
)

FILE.write_text(txt)

print("DONE: Rotation Engine v2 decay + trend + confidence installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
