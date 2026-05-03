from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
FILE = ROOT / "profit_lab_routes.py"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

backup = ROOT / f"profit_lab_routes.py.bak_rotation_fix_v3_{STAMP}"
shutil.copy2(FILE, backup)
print(f"BACKUP | {backup.name}")

txt = FILE.read_text()

# 1) Add/replace robust rotation engine function
start = txt.find("def build_rotation_engine_v1")
end = txt.find("\ndef lab_snapshot():", start)

engine = r'''
def build_rotation_engine_v1(s, positions):
    metrics = s.get("metrics") or {}
    latest = s.get("latest") or {}
    closed = int(metrics.get("closed_trades") or 0)
    open_pl = float(latest.get("open_pl") or 0)

    positions = positions or []

    if not positions:
        return {
            "score": 0,
            "state": "IDLE",
            "pressure": "LOW",
            "readiness": "NOT READY",
            "decision": "WAIT",
            "weakest": "-",
            "weakest_pnl": 0,
            "weakest_pnl_pct": 0,
            "best_offset": "-",
            "best_offset_pnl": 0,
            "best_offset_pnl_pct": 0,
            "suggested_move": "No open positions to evaluate.",
            "reason": "Rotation engine is observing only."
        }

    def pl(p):
        return float(p.get("unrealized_pl") or p.get("open_pl") or p.get("pnl") or 0)

    def plpc(p):
        return float(p.get("unrealized_plpc") or p.get("pl_pct") or p.get("pnl_pct") or 0)

    weakest = sorted(positions, key=lambda p: plpc(p))[0]
    strongest = sorted(positions, key=lambda p: plpc(p))[-1]

    losers = [p for p in positions if pl(p) < 0]
    winners = [p for p in positions if pl(p) > 0]

    weakest_pl = pl(weakest)
    weakest_pct = plpc(weakest)

    severity = min(40, abs(min(weakest_pct, 0)) * 8)
    dollar_drag = min(25, abs(min(weakest_pl, 0)) / 35)
    portfolio_drag = min(15, abs(min(open_pl, 0)) / 40)
    mix_drag = 10 if len(losers) > len(winners) else 0

    score = int(min(100, severity + dollar_drag + portfolio_drag + mix_drag))

    if score >= 75:
        state = "ROTATION PRESSURE"
        pressure = "HIGH"
    elif score >= 50:
        state = "WATCH"
        pressure = "MEDIUM"
    else:
        state = "HOLD"
        pressure = "LOW"

    readiness = "READY TO REVIEW" if closed >= 15 else "NOT READY"

    if closed < 15:
        decision = "DO NOT ROTATE"
        suggested = "Suggestion-only. Need 15–20 closed trades before automation."
    elif score >= 75:
        decision = "REVIEW ROTATION"
        suggested = "Rotation pressure is high. Review before any execution."
    elif score >= 50:
        decision = "WATCH"
        suggested = "Monitor weakest position. Pressure is building."
    else:
        decision = "HOLD"
        suggested = "Rotation pressure is low."

    return {
        "score": score,
        "state": state,
        "pressure": pressure,
        "readiness": readiness,
        "decision": decision,
        "weakest": weakest.get("symbol", "-"),
        "weakest_pnl": round(weakest_pl, 2),
        "weakest_pnl_pct": round(weakest_pct, 2),
        "best_offset": strongest.get("symbol", "-"),
        "best_offset_pnl": round(pl(strongest), 2),
        "best_offset_pnl_pct": round(plpc(strongest), 2),
        "suggested_move": suggested,
        "reason": f"{weakest.get('symbol','-')} is weakest at {weakest_pct:.2f}% / ${weakest_pl:.2f}. {len(winners)} winners / {len(losers)} losers."
    }

'''

if start != -1 and end != -1:
    txt = txt[:start] + engine + txt[end:]
else:
    txt = txt.replace("def lab_snapshot():", engine + "\ndef lab_snapshot():")

# 2) Ensure rotation_engine is inside lab dict using SAME positions variable
if '"rotation_engine": build_rotation_engine_v1(s, positions),' not in txt:
    txt = txt.replace(
        '"positions": positions,',
        '"positions": positions,\n        "rotation_engine": build_rotation_engine_v1(s, positions),'
    )

# 3) Fix JS renderer if needed
if "const engine=lab.rotation_engine||{};" not in txt:
    txt = txt.replace(
        'document.getElementById("decisionReplay").innerHTML=(lab.decision_replay||[]).map(x=>`',
        '''const engine=lab.rotation_engine||{};
  const rotScore=document.getElementById("rotScore");
  if(rotScore){
    rotScore.textContent=(engine.score ?? "--") + "/100";
    rotScore.className="value " + ((engine.score||0)>=75 ? "bad" : (engine.score||0)>=50 ? "warn" : "good");
    document.getElementById("rotState").textContent=engine.state||"--";
    document.getElementById("rotPressure").textContent=engine.pressure||"--";
    document.getElementById("rotReadiness").textContent=engine.readiness||"--";
    if(document.getElementById("rotDecision")){
      document.getElementById("rotDecision").textContent=engine.decision||"--";
    }
    document.getElementById("rotDetails").textContent=`Weakest: ${engine.weakest||"-"} (${money(engine.weakest_pnl||0)} / ${pct(engine.weakest_pnl_pct||0)}) · Best Offset: ${engine.best_offset||"-"} (${money(engine.best_offset_pnl||0)} / ${pct(engine.best_offset_pnl_pct||0)})`;
    document.getElementById("rotMove").textContent=engine.suggested_move||"Keep monitoring.";
  }

  document.getElementById("decisionReplay").innerHTML=(lab.decision_replay||[]).map(x=>`'''
    )

FILE.write_text(txt)

print("DONE: Rotation Fix + Decision System v3 installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
