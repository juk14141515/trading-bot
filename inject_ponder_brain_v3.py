from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_ponder_brain_v3_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

# === UPGRADE PONDER SUMMARY ===
txt = txt.replace(
    "let summary=",
    """
let worst = null;
if(positions.length){
  worst = positions.reduce((a,b)=> (Number(a.unrealized_pl||0) < Number(b.unrealized_pl||0) ? a : b));
}

let totalPositionValue = positions.reduce((s,p)=> s + Number(p.market_value||0),0);
let losingValue = positions.filter(p=>Number(p.unrealized_pl||0)<0)
                           .reduce((s,p)=> s + Number(p.market_value||0),0);

let riskRatio = totalPositionValue ? (losingValue / totalPositionValue) : 0;

let riskLevel = "LOW";
if(riskRatio > 0.6) riskLevel = "HIGH";
else if(riskRatio > 0.3) riskLevel = "MEDIUM";

let summary=
"""
)

# === ADD RISK + WEAKNESS INTO SUMMARY TEXT ===
txt = txt.replace(
    "Open P/L:",
    """Risk Level: ${riskLevel} | Open P/L:"""
)

txt = txt.replace(
    "Weakest position:",
    """Weakest position: ${worst ? worst.symbol : "N/A"} (P/L: $${worst ? Number(worst.unrealized_pl||0).toFixed(2) : "0"}) |"""
)

# === ADD CAPITAL EFFICIENCY ===
if "Capital Efficiency" not in txt:
    txt = txt.replace(
        '<div class="card" style="margin-top:16px">',
        '''
<div class="card" style="margin-top:16px">
  <h2>💰 Capital Efficiency</h2>
  <div class="grid">
    <div><div class="label">Capital Used</div><div id="capUsed" class="value">--</div></div>
    <div><div class="label">Losing Exposure</div><div id="capLosing" class="value">--</div></div>
    <div><div class="label">Risk Level</div><div id="capRisk" class="value">--</div></div>
  </div>
</div>

<div class="card" style="margin-top:16px">'''
    )

# === ADD JS UPDATE LOGIC ===
if "updateCapitalStats" not in txt:
    txt = txt.replace(
        "function ponderPerformanceInsight",
        """
function updateCapitalStats(d){
  const lab=d.lab||{};
  const positions=lab.positions||[];

  const total=positions.reduce((s,p)=>s+Number(p.market_value||0),0);
  const losing=positions.filter(p=>Number(p.unrealized_pl||0)<0)
                        .reduce((s,p)=>s+Number(p.market_value||0),0);

  let ratio = total ? losing/total : 0;

  let risk="LOW";
  if(ratio > 0.6) risk="HIGH";
  else if(ratio > 0.3) risk="MEDIUM";

  if(document.getElementById("capUsed")){
    document.getElementById("capUsed").textContent="$"+total.toFixed(0);
  }
  if(document.getElementById("capLosing")){
    document.getElementById("capLosing").textContent="$"+losing.toFixed(0);
  }
  if(document.getElementById("capRisk")){
    document.getElementById("capRisk").textContent=risk;
  }
}

function ponderPerformanceInsight"""
    )

# === CALL IT ===
txt = txt.replace(
    "ponderPerformanceInsight(lastProfitLabData);",
    """ponderPerformanceInsight(lastProfitLabData);
  updateCapitalStats(lastProfitLabData);"""
)

p.write_text(txt)

print("DONE: Ponder Brain V3 (Risk + Capital Intelligence) installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
