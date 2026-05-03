from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
FILE = ROOT / "profit_lab_routes.py"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

backup = ROOT / f"profit_lab_routes.py.bak_rotation_engine_v2_{STAMP}"
shutil.copy2(FILE, backup)
print(f"BACKUP | {backup.name}")

txt = FILE.read_text()

# Replace or add connected rotation engine
start = txt.find("def build_rotation_engine_v1")
end = txt.find("\ndef lab_snapshot():", start)

engine_code = r'''
def build_rotation_engine_v1(s, positions):
    metrics = s.get("metrics") or {}
    closed = int(metrics.get("closed_trades") or 0)
    latest = s.get("latest") or {}

    open_pl = float(latest.get("open_pl") or 0)

    if not positions:
        return {
            "score": 0,
            "state": "IDLE",
            "pressure": "LOW",
            "readiness": "NOT READY",
            "weakest": "-",
            "weakest_pnl": 0,
            "weakest_pnl_pct": 0,
            "best_offset": "-",
            "best_offset_pnl": 0,
            "best_offset_pnl_pct": 0,
            "decision": "WAIT",
            "suggested_move": "No open positions to evaluate.",
            "reason": "Rotation engine is observing only."
        }

    weakest = sorted(positions, key=lambda p: float(p.get("unrealized_plpc", 0) or 0))[0]
    strongest = sorted(positions, key=lambda p: float(p.get("unrealized_plpc", 0) or 0))[-1]

    losers = [p for p in positions if float(p.get("unrealized_pl", 0) or 0) < 0]
    winners = [p for p in positions if float(p.get("unrealized_pl", 0) or 0) > 0]

    pnl_pct = float(weakest.get("unrealized_plpc", 0) or 0)
    pnl = float(weakest.get("unrealized_pl", 0) or 0)
    losing_seconds = float(weakest.get("held_losing_seconds", 0) or 0)

    severity = min(40, abs(min(pnl_pct, 0)) * 8)
    dollar_drag = min(25, abs(min(pnl, 0)) / 35)
    time_drag = min(20, losing_seconds / 3600 * 5)
    mix_drag = 10 if len(losers) > len(winners) else 0
    portfolio_drag = min(10, abs(min(open_pl, 0)) / 50)

    score = int(min(100, severity + dollar_drag + time_drag + mix_drag + portfolio_drag))

    if score >= 75:
        pressure = "HIGH"
        state = "ROTATION PRESSURE"
    elif score >= 50:
        pressure = "MEDIUM"
        state = "WATCH"
    else:
        pressure = "LOW"
        state = "HOLD"

    readiness = "READY TO REVIEW" if closed >= 15 else "NOT READY"

    if readiness != "READY TO REVIEW":
        decision = "DO NOT ROTATE"
        suggested = "Collect more closed trades before enabling automation."
    elif score >= 75:
        decision = "REVIEW ROTATION"
        suggested = "Rotation may be worth reviewing, but execution should still require confirmation."
    elif score >= 50:
        decision = "WATCH"
        suggested = "Monitor weakest position; pressure is building."
    else:
        decision = "HOLD"
        suggested = "No rotation needed right now."

    return {
        "score": score,
        "state": state,
        "pressure": pressure,
        "readiness": readiness,
        "weakest": weakest.get("symbol", "-"),
        "weakest_pnl": round(pnl, 2),
        "weakest_pnl_pct": round(pnl_pct, 2),
        "best_offset": strongest.get("symbol", "-"),
        "best_offset_pnl": round(float(strongest.get("unrealized_pl", 0) or 0), 2),
        "best_offset_pnl_pct": round(float(strongest.get("unrealized_plpc", 0) or 0), 2),
        "decision": decision,
        "suggested_move": suggested,
        "reason": f"{weakest.get('symbol','-')} is weakest at {pnl_pct:.2f}% / ${pnl:.2f}. {len(winners)} winners / {len(losers)} losers."
    }
'''

if start != -1 and end != -1:
    txt = txt[:start] + engine_code + txt[end:]
else:
    txt = txt.replace("def lab_snapshot():", engine_code + "\ndef lab_snapshot():")

# Ensure lab JSON includes engine
if '"rotation_engine": build_rotation_engine_v1' not in txt:
    txt = txt.replace(
        '"positions": positions,',
        '"positions": positions,\n        "rotation_engine": build_rotation_engine_v1(s, positions),'
    )

# Make UI display real decision
if "rotDecision" not in txt:
    txt = txt.replace(
        '<div style="margin-top:8px;font-weight:900" id="rotMove">No action.</div>',
        '<div class="label" style="margin-top:12px">Decision</div><div id="rotDecision" class="value">--</div><div style="margin-top:8px;font-weight:900" id="rotMove">No action.</div>'
    )

if 'document.getElementById("rotDecision")' not in txt:
    txt = txt.replace(
        'document.getElementById("rotMove").textContent=engine.suggested_move||"Keep monitoring.";',
        '''document.getElementById("rotDecision").textContent=engine.decision||"--";
    document.getElementById("rotDecision").className="value " + ((engine.decision||"").includes("DO NOT") ? "warn" : (engine.decision||"").includes("REVIEW") ? "bad" : "good");
    document.getElementById("rotMove").textContent=engine.suggested_move||"Keep monitoring.";'''
    )

FILE.write_text(txt)

print("DONE: Connected Rotation Engine v2 installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
