from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_ponder_brain_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

if "Ponder Brain" not in txt:
    txt = txt.replace(
        '<div class="layout">',
        '''
  <div class="card" style="margin-top:16px">
    <h2>🐾 Ponder Brain</h2>
    <div id="ponderSummary" class="muted">Ponder is reading the graph...</div>
    <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
      <button onclick="askPonder('graph')">What does the graph mean?</button>
      <button onclick="askPonder('risk')">How risky is this?</button>
      <button onclick="askPonder('positions')">Which position is weakest?</button>
      <button onclick="askPonder('suggest')">Any suggestions?</button>
    </div>
    <div style="margin-top:12px;display:flex;gap:8px">
      <input id="ponderQuestion" placeholder="Ask Ponder about the graph, risk, positions, or strategy..." style="flex:1;padding:10px;border-radius:10px;border:1px solid var(--border);background:#0b1225;color:white">
      <button onclick="askPonder()">Ask</button>
    </div>
    <pre id="ponderAnswer" style="margin-top:12px;white-space:pre-wrap;max-height:220px;overflow:auto">Ask me something like: “Why is the graph down?” or “What should I watch tomorrow?”</pre>
  </div>

  <div class="layout">'''
    )

if "function askPonder" not in txt:
    txt = txt.replace(
        "let chart=null;",
        "let chart=null;\nlet lastProfitLabData=null;"
    )

    txt = txt.replace(
        "const d=await r.json();",
        "const d=await r.json();\n  lastProfitLabData=d;"
    )

    txt = txt.replace(
        "load();\nsetInterval(load,10000);",
        r'''
function ponderInsight(d){
  if(!d) return "No data loaded yet.";
  const l=d.latest||{}, h=d.health||{}, lab=d.lab||{}, eq=d.equity||[];
  const positions=lab.positions||[];
  const open=Number(l.open_pl||0);
  const health=Number(h.score||0);
  let trend="flat";
  if(eq.length>3){
    const first=Number(eq[0].portfolio_value||0);
    const last=Number(eq[eq.length-1].portfolio_value||0);
    if(last>first) trend="up";
    if(last<first) trend="down";
  }
  let weakest="None";
  if(positions.length){
    weakest=positions.slice().sort((a,b)=>Number(a.unrealized_pl||0)-Number(b.unrealized_pl||0))[0].symbol;
  }
  return `Ponder Summary 🐾
Health: ${health}/100
Equity trend: ${trend}
Open P/L: $${open.toFixed(2)}
Open positions: ${positions.length}
Weakest position: ${weakest}

Current read:
${health>=75 ? "System health is decent." : "System should stay defensive."}
${open<0 ? "Open P/L is negative, so risk control matters right now." : "Open P/L is positive or neutral."}
${positions.length ? "Watch the weakest holding and whether rotation/guard logic reacts." : "No open positions to judge yet."}`;
}

function askPonder(kind){
  const d=lastProfitLabData;
  const q=(kind || document.getElementById("ponderQuestion")?.value || "").toLowerCase();
  const ans=document.getElementById("ponderAnswer");
  if(!ans) return;

  if(!d){
    ans.textContent="Ponder is still loading data. Try again in a few seconds.";
    return;
  }

  const l=d.latest||{}, h=d.health||{}, lab=d.lab||{}, eq=d.equity||[];
  const positions=lab.positions||[];
  const open=Number(l.open_pl||0);
  const health=Number(h.score||0);

  let first=eq.length?Number(eq[0].portfolio_value||0):0;
  let last=eq.length?Number(eq[eq.length-1].portfolio_value||0):0;
  let change=last-first;

  if(q.includes("graph") || q.includes("equity") || q.includes("down") || q.includes("up")){
    ans.textContent=`The graph is your portfolio value over time.

Start: $${first.toFixed(2)}
Latest: $${last.toFixed(2)}
Change: $${change.toFixed(2)}

Ponder’s read:
${change>=0 ? "The account is slightly up over this window." : "The account is down over this window."}
The sharp moves are mostly unrealized position value changes, not necessarily closed profit yet. Since closed trades are still low, this is still learning/data collection mode.`;
  } else if(q.includes("risk") || q.includes("health")){
    ans.textContent=`Risk read:

AI Health: ${health}/100
Open P/L: $${open.toFixed(2)}
Open positions: ${positions.length}

Ponder’s read:
${health>=80 ? "Health is strong, but do not overtrust it until more closed trades exist." : health>=60 ? "Health is acceptable, but defensive behavior is still smart." : "Health is weak; reduce risk and review exits."}
${open<0 ? "Because open P/L is negative, watch the kill switch and weakest position." : "Open P/L is not pressuring the system right now."}`;
  } else if(q.includes("position") || q.includes("weak") || q.includes("nvda") || q.includes("aapl") || q.includes("amzn")){
    if(!positions.length){
      ans.textContent="No open positions right now, so Ponder has nothing to rank.";
    } else {
      const sorted=positions.slice().sort((a,b)=>Number(a.unrealized_pl||0)-Number(b.unrealized_pl||0));
      const weak=sorted[0];
      const best=sorted[sorted.length-1];
      ans.textContent=`Position read:

Weakest: ${weak.symbol} | P/L $${Number(weak.unrealized_pl||0).toFixed(2)} | ${Number(weak.unrealized_plpc||0).toFixed(2)}%
Best: ${best.symbol} | P/L $${Number(best.unrealized_pl||0).toFixed(2)} | ${Number(best.unrealized_plpc||0).toFixed(2)}%

Ponder’s read:
The weakest position is the one to watch for trade guard, rotation, or stale-position logic.`;
    }
  } else if(q.includes("suggest") || q.includes("should") || q.includes("next")){
    ans.textContent=`Suggestions:

1. Keep collecting data until you have at least 20 closed trades.
2. Watch whether the bad-trade guard cuts weak losers.
3. Watch whether rotation frees capital when slots are full.
4. Do not over-optimize yet — closed-trade data is still too small.
5. Next useful upgrade: log score breakdown per trade so Ponder can explain WHY trades won or lost.`;
  } else {
    ans.textContent=ponderInsight(d);
  }
}

setInterval(()=> {
  const el=document.getElementById("ponderSummary");
  if(el && lastProfitLabData){ el.textContent=ponderInsight(lastProfitLabData); }
}, 3000);

load();
setInterval(load,10000);'''
    )

if "button" not in txt:
    txt = txt.replace(
        "</style>",
        """
button{padding:9px 12px;border-radius:10px;border:1px solid var(--border);background:#0b1225;color:white;cursor:pointer}
button:hover{border-color:var(--blue)}
</style>"""
    )

p.write_text(txt)
print("DONE: Ponder Brain Panel installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
