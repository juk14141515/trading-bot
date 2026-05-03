from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
FILE = ROOT / "profit_lab_routes.py"

backup = ROOT / f"profit_lab_routes.py.bak_rotation_engine_v1_{STAMP}"
shutil.copy2(FILE, backup)
print(f"BACKUP | {backup.name}")

txt = FILE.read_text()

# ----------------------------
# Backend: Rotation Engine v1
# ----------------------------
if "def build_rotation_engine_v1" not in txt:
    txt = txt.replace(
        "def lab_snapshot():",
        r'''
def build_rotation_engine_v1(s, positions):
    metrics = s.get("metrics") or {}
    closed = int(metrics.get("closed_trades") or 0)

    if not positions:
        return {
            "score": 0,
            "state": "IDLE",
            "pressure": "LOW",
            "weakest": "-",
            "best_offset": "-",
            "readiness": "NOT READY",
            "suggested_move": "No open positions to evaluate.",
            "reason": "Rotation engine is observing only."
        }

    weakest = sorted(positions, key=lambda p: float(p.get("unrealized_plpc", 0) or 0))[0]
    strongest = sorted(positions, key=lambda p: float(p.get("unrealized_plpc", 0) or 0))[-1]

    pnl_pct = float(weakest.get("unrealized_plpc", 0) or 0)
    pnl = float(weakest.get("unrealized_pl", 0) or 0)
    losing_seconds = float(weakest.get("held_losing_seconds", 0) or 0)

    severity = min(45, abs(min(pnl_pct, 0)) * 9)
    dollar_drag = min(25, abs(min(pnl, 0)) / 35)
    time_drag = min(20, losing_seconds / 3600 * 5)
    mix_drag = 10 if len([p for p in positions if float(p.get("unrealized_pl", 0) or 0) < 0]) > len(positions) / 2 else 0

    score = int(min(100, severity + dollar_drag + time_drag + mix_drag))

    if score >= 70:
        state = "ROTATION PRESSURE"
        pressure = "HIGH"
    elif score >= 45:
        state = "WATCH"
        pressure = "MEDIUM"
    else:
        state = "HOLD"
        pressure = "LOW"

    readiness = "READY TO REVIEW" if closed >= 15 else "NOT READY"

    if readiness != "READY TO REVIEW":
        suggested = "Do not execute rotation yet. Keep collecting closed-trade data."
    elif score >= 70:
        suggested = "Review controlled rotation rules before enabling execution."
    elif score >= 45:
        suggested = "Monitor weakness. Rotation pressure is building."
    else:
        suggested = "Hold. Rotation pressure is low."

    return {
        "score": score,
        "state": state,
        "pressure": pressure,
        "weakest": weakest.get("symbol", "-"),
        "weakest_pnl": round(pnl, 2),
        "weakest_pnl_pct": round(pnl_pct, 2),
        "best_offset": strongest.get("symbol", "-"),
        "best_offset_pnl": round(float(strongest.get("unrealized_pl", 0) or 0), 2),
        "best_offset_pnl_pct": round(float(strongest.get("unrealized_plpc", 0) or 0), 2),
        "readiness": readiness,
        "suggested_move": suggested,
        "reason": f"Weakest position is {weakest.get('symbol', '-')} at {pnl_pct:.2f}% / ${pnl:.2f}."
    }

def lab_snapshot():'''
    )

if '"rotation_engine": build_rotation_engine_v1' not in txt:
    txt = txt.replace(
        '"ponder_verdict": build_ponder_verdict(s, positions),',
        '"ponder_verdict": build_ponder_verdict(s, positions),\n        "rotation_engine": build_rotation_engine_v1(s, positions),'
    )

# ----------------------------
# UI: Rotation Engine card
# ----------------------------
if "Rotation Engine v1" not in txt:
    txt = txt.replace(
        '<div class="layout">',
        '''
  <div class="card" style="margin-top:16px">
    <h2>🧠 Rotation Engine v1</h2>
    <div class="grid">
      <div><div class="label">Score</div><div id="rotScore" class="value">--</div></div>
      <div><div class="label">State</div><div id="rotState" class="value">--</div></div>
      <div><div class="label">Pressure</div><div id="rotPressure" class="value">--</div></div>
      <div><div class="label">Readiness</div><div id="rotReadiness" class="value">--</div></div>
    </div>
    <div style="margin-top:14px" class="muted" id="rotDetails">Waiting for rotation engine...</div>
    <div style="margin-top:8px;font-weight:900" id="rotMove">No action.</div>
  </div>

  <div class="layout">'''
    )

# ----------------------------
# JS renderer
# ----------------------------
if "rotScore" in txt and "lab.rotation_engine" not in txt:
    txt = txt.replace(
        'document.getElementById("decisionReplay").innerHTML=(lab.decision_replay||[]).map(x=>`',
        '''const engine=lab.rotation_engine||{};
  const rotScore=document.getElementById("rotScore");
  if(rotScore){
    rotScore.textContent=(engine.score ?? "--") + "/100";
    rotScore.className="value " + ((engine.score||0)>=70 ? "bad" : (engine.score||0)>=45 ? "warn" : "good");
    document.getElementById("rotState").textContent=engine.state||"--";
    document.getElementById("rotPressure").textContent=engine.pressure||"--";
    document.getElementById("rotReadiness").textContent=engine.readiness||"--";
    document.getElementById("rotDetails").textContent=`Weakest: ${engine.weakest||"-"} (${money(engine.weakest_pnl||0)} / ${pct(engine.weakest_pnl_pct||0)}) · Best Offset: ${engine.best_offset||"-"} (${money(engine.best_offset_pnl||0)} / ${pct(engine.best_offset_pnl_pct||0)})`;
    document.getElementById("rotMove").textContent=engine.suggested_move||"Keep monitoring.";
  }

  document.getElementById("decisionReplay").innerHTML=(lab.decision_replay||[]).map(x=>`'''
    )

# Add Ponder button
if "Rotation engine?" not in txt:
    txt = txt.replace(
        '<button onclick="askPonder(\'rotation\')">Rotation analysis?</button>',
        '''<button onclick="askPonder('rotation')">Rotation analysis?</button>
      <button onclick="askPonder('engine')">Rotation engine?</button>'''
    )

# Add Ponder answer branch
if "Rotation Engine v1 Analysis" not in txt:
    txt = txt.replace(
        '''} else if(q.includes("rotation") || q.includes("rotate")){''',
        r'''} else if(q.includes("engine")){
    const e = lab.rotation_engine || {};
    ans.textContent=`Rotation Engine v1 Analysis 🐾

Score: ${e.score ?? "--"}/100
State: ${e.state || "-"}
Pressure: ${e.pressure || "-"}
Readiness: ${e.readiness || "-"}

Weakest:
${e.weakest || "-"} | ${money(e.weakest_pnl || 0)} | ${pct(e.weakest_pnl_pct || 0)}

Best offset:
${e.best_offset || "-"} | ${money(e.best_offset_pnl || 0)} | ${pct(e.best_offset_pnl_pct || 0)}

Suggested move:
${e.suggested_move || "Keep monitoring."}

Important:
This is still read-only. It does not execute trades.`;

  } else if(q.includes("rotation") || q.includes("rotate")){'''
    )

FILE.write_text(txt)

print("DONE: Rotation Engine v1 installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
