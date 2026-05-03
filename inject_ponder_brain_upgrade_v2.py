from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_ponder_brain_upgrade_v2_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

# Add button
if "What changed recently?" not in txt:
    txt = txt.replace(
        '<button onclick="askPonder(\'suggest\')">Any suggestions?</button>',
        '''<button onclick="askPonder('suggest')">Any suggestions?</button>
      <button onclick="askPonder('change')">What changed recently?</button>'''
    )

# Add Performance Insight Panel below Ponder Brain
if "Performance Insight" not in txt:
    txt = txt.replace(
        '<div class="layout">',
        '''
  <div class="card" style="margin-top:16px">
    <h2>📊 Performance Insight</h2>
    <div class="grid">
      <div><div class="label">Closed Trades</div><div id="insightClosed" class="value">0</div></div>
      <div><div class="label">Win Rate</div><div id="insightWinRate" class="value">0%</div></div>
      <div><div class="label">Avg Win / Loss</div><div id="insightAvg" class="value">$0 / $0</div></div>
      <div><div class="label">Ponder Read</div><div id="insightRead" class="muted">Waiting for data...</div></div>
    </div>
  </div>

  <div class="layout">'''
    )

# Add smarter JS
if "function ponderPerformanceInsight" not in txt:
    txt = txt.replace(
        "function ponderInsight(d){",
        r'''
function ponderPerformanceInsight(d){
  if(!d) return;
  const m=d.metrics||{}, lab=d.lab||{}, positions=lab.positions||[];
  const closed=Number(m.closed_trades||0);
  const winRate=Number(m.win_rate||0);
  const avgWin=Number(m.avg_win||0);
  const avgLoss=Number(m.avg_loss||0);
  const losing=positions.filter(p=>Number(p.unrealized_pl||0)<0).length;
  const winners=positions.length-losing;

  let read="Learning mode: not enough closed trades yet.";
  if(closed >= 5){
    if(winRate >= 55 && Number(m.net_closed_pnl||0) >= 0){
      read="Closed-trade performance is healthy so far.";
    } else if(winRate < 45){
      read="Win rate is weak. Review entries, exits, and score thresholds.";
    } else {
      read="Mixed results. Keep collecting trades before changing weights.";
    }
  }

  if(positions.length && losing > winners){
    read += " More open positions are losing than winning.";
  }

  const elClosed=document.getElementById("insightClosed");
  const elWin=document.getElementById("insightWinRate");
  const elAvg=document.getElementById("insightAvg");
  const elRead=document.getElementById("insightRead");

  if(elClosed) elClosed.textContent=closed;
  if(elWin) elWin.textContent=winRate.toFixed(2)+"%";
  if(elAvg) elAvg.textContent="$"+avgWin.toFixed(2)+" / $"+avgLoss.toFixed(2);
  if(elRead) elRead.textContent=read;
}

function ponderInsight(d){'''
    )

# Improve suggestions block
txt = txt.replace(
    '''ans.textContent=`Suggestions:

1. Keep collecting data until you have at least 20 closed trades.
2. Watch whether the bad-trade guard cuts weak losers.
3. Watch whether rotation frees capital when slots are full.
4. Do not over-optimize yet — closed-trade data is still too small.
5. Next useful upgrade: log score breakdown per trade so Ponder can explain WHY trades won or lost.`;''',
    r'''const losing = positions.filter(p => Number(p.unrealized_pl||0) < 0).length;
    const winners = positions.length - losing;
    const m=d.metrics||{};
    ans.textContent=`Ponder Strategy Suggestions 🐾

Current state:
- Winners open: ${winners}
- Losers open: ${losing}
- Open P/L: $${open.toFixed(2)}
- Closed trades: ${m.closed_trades||0}
- Closed win rate: ${Number(m.win_rate||0).toFixed(2)}%

Ponder thinks:
${losing > winners ? "- More positions are losing than winning — exits or entries may need review.\\n" : "- Open position balance is not worse than neutral.\\n"}
${open < 0 ? "- Overall unrealized P/L is negative, so risk control matters.\\n" : "- Open P/L is not currently pressuring the system.\\n"}
${health < 70 ? "- Health is dropping — defensive mode is appropriate.\\n" : "- Health is acceptable, but more closed trades are needed.\\n"}
${positions.length >= 3 ? "- Capital is tied up — rotation logic is important.\\n" : "- Position slots are not fully loaded.\\n"}

Best next move:
Keep collecting data, then tune exits and rotation before changing entry scoring.`;'''
)

# Add change branch before suggestions or before final else
if "Recent Change Analysis" not in txt:
    txt = txt.replace(
        '''} else if(q.includes("suggest") || q.includes("should") || q.includes("next")){''',
        r'''} else if(q.includes("change") || q.includes("recent")){
    if(eq.length < 5){
      ans.textContent="Not enough equity points yet to detect recent change.";
      return;
    }

    let prev = Number(eq[eq.length-5].portfolio_value||0);
    let curr = Number(eq[eq.length-1].portfolio_value||0);
    let diff = curr - prev;

    let prevOpen = Number(eq[eq.length-5].open_pl||0);
    let currOpen = Number(eq[eq.length-1].open_pl||0);
    let openDiff = currOpen - prevOpen;

    ans.textContent=`Recent Change Analysis 🐾

Portfolio moved: $${diff.toFixed(2)}
Open P/L moved: $${openDiff.toFixed(2)}

Ponder’s read:
${diff > 0 ? "Recent account movement is positive." : "Recent account movement is negative or flat."}
${openDiff > 0 ? "Open positions improved recently." : "Open positions weakened recently."}

Watch:
- Whether weakest position improves or worsens
- Whether trade guard reacts if a loser keeps falling
- Whether rotation frees capital once market opens`;

  } else if(q.includes("suggest") || q.includes("should") || q.includes("next")){'''
    )

# Call performance insight after data load
if "ponderPerformanceInsight(lastProfitLabData)" not in txt:
    txt = txt.replace(
        '''lastProfitLabData=d;''',
        '''lastProfitLabData=d;
  ponderPerformanceInsight(lastProfitLabData);'''
    )

p.write_text(txt)

print("DONE: Ponder Brain Upgrade V2 installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
