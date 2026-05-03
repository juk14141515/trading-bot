from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_decision_feed_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

# Add backend decision/candidate helpers
if "def build_decision_replay" not in txt:
    txt = txt.replace(
        "def lab_snapshot():",
        r'''
def build_decision_replay(s):
    rows = []
    for line in s.get("recent_logs", [])[-160:]:
        label = None
        tone = "neutral"

        if "BUY DECISION" in line:
            label = "BUY DECISION"
            tone = "good"
        elif "SKIP BUY" in line:
            label = "SKIP BUY"
            tone = "warn"
        elif "CONFIDENCE" in line:
            label = "CONFIDENCE"
            tone = "info"
        elif "SCANNER" in line:
            label = "SCANNER"
            tone = "info"
        elif "ROTATION" in line:
            label = "ROTATION"
            tone = "warn"
        elif "TRADE GUARD" in line or "FORCE EXIT" in line:
            label = "RISK GUARD"
            tone = "bad"
        elif "SELL" in line:
            label = "SELL"
            tone = "bad"

        if label:
            rows.append({
                "label": label,
                "tone": tone,
                "line": line
            })

    return rows[-80:]


def build_candidate_feed(s):
    candidates = []
    logs = s.get("recent_logs", [])[-250:]

    for line in logs:
        upper = line.upper()

        if any(k in upper for k in ["CONFIDENCE", "BUY DECISION", "SKIP BUY", "SCANNER", "CANDIDATE"]):
            symbol = "-"
            score = "-"

            parts = line.replace("|", " ").replace(",", " ").split()
            for part in parts:
                clean = part.strip().upper()
                if clean.isalpha() and 1 <= len(clean) <= 5 and clean not in [
                    "BUY","SELL","SKIP","NEW","CYCLE","MARKET","CLOSED","SCANNER",
                    "CONFIDENCE","DECISION","ROTATION","REASON"
                ]:
                    symbol = clean
                    break

            for part in parts:
                if "score=" in part.lower():
                    score = part.split("=")[-1]
                elif "confidence=" in part.lower():
                    score = part.split("=")[-1]

            reason = "observed"
            if "market closed" in line.lower():
                reason = "market closed"
            elif "max positions" in line.lower():
                reason = "slots full"
            elif "threshold" in line.lower():
                reason = "below threshold"
            elif "rotation" in line.lower():
                reason = "rotation check"
            elif "no buys" in line.lower():
                reason = "no buy selected"

            candidates.append({
                "symbol": symbol,
                "score": score,
                "reason": reason,
                "line": line
            })

    return candidates[-40:]


def lab_snapshot():'''
    )

if '"decision_replay": build_decision_replay(s)' not in txt:
    txt = txt.replace(
        '"win_rate_today": round((wins / len(sells) * 100), 2) if sells else 0,',
        '''"win_rate_today": round((wins / len(sells) * 100), 2) if sells else 0,
        "decision_replay": build_decision_replay(s),
        "candidate_feed": build_candidate_feed(s),'''
    )

# Add UI sections
if "Decision Replay" not in txt:
    txt = txt.replace(
        '<div class="card">\n  <h3>Live Positions</h3>',
        '''<div class="card">
  <h3>Decision Replay</h3>
  <div id="decisionReplay" style="max-height:260px;overflow:auto;font-family:monospace;font-size:13px"></div>
</div>

<div class="card">
  <h3>Candidate Feed</h3>
  <table style="width:100%">
    <thead>
      <tr><th>Symbol</th><th>Score</th><th>Reason</th></tr>
    </thead>
    <tbody id="candidateFeed"></tbody>
  </table>
</div>

<div class="card">
  <h3>Live Positions</h3>'''
    )

# Add styling for replay chips
if ".chip" not in txt:
    txt = txt.replace(
        "</style>",
        '''
.chip{display:inline-block;border-radius:999px;padding:3px 8px;margin-right:8px;font-weight:bold;font-size:11px}
.good{color:#4ade80}.bad{color:#f87171}.warn{color:#facc15}.info{color:#93c5fd}.neutral{color:#cbd5e1}
.chip.good{background:rgba(74,222,128,.14)}.chip.bad{background:rgba(248,113,113,.14)}.chip.warn{background:rgba(250,204,21,.14)}.chip.info{background:rgba(147,197,253,.14)}.chip.neutral{background:rgba(203,213,225,.14)}
</style>'''
    )

# Add JS rendering
if "decisionReplay" in txt and "lab.decision_replay" not in txt:
    txt = txt.replace(
        'document.getElementById("positions").innerHTML =\n    rows || "<tr><td colspan=\'3\'>No positions</td></tr>";',
        '''document.getElementById("positions").innerHTML =
    rows || "<tr><td colspan='3'>No positions</td></tr>";

  let replayEl = document.getElementById("decisionReplay");
  if(replayEl){
    replayEl.innerHTML = (lab.decision_replay || []).map(x =>
      `<div style="padding:7px 0;border-bottom:1px solid rgba(255,255,255,.08)">
        <span class="chip ${x.tone||'neutral'}">${x.label||'LOG'}</span>
        <span class="${x.tone||'neutral'}">${x.line||''}</span>
      </div>`
    ).join("") || "<div>No decision replay yet.</div>";
  }

  let candidateEl = document.getElementById("candidateFeed");
  if(candidateEl){
    candidateEl.innerHTML = (lab.candidate_feed || []).map(x =>
      `<tr>
        <td>${x.symbol||"-"}</td>
        <td>${x.score||"-"}</td>
        <td>${x.reason||"-"}</td>
      </tr>`
    ).join("") || "<tr><td colspan='3'>No candidates yet.</td></tr>";
  }'''
    )

p.write_text(txt)

print("DONE: Decision Replay + Candidate Feed installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
