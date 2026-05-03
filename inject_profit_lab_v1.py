from pathlib import Path
from datetime import datetime, date
import shutil, re

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_profit_lab_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("web_dashboard.py")

(ROOT / "profit_lab_routes.py").write_text(r'''
from flask import Blueprint, jsonify, render_template_string
from profit_ops_analytics import snapshot

profit_lab_bp = Blueprint("profit_lab", __name__)

def lab_snapshot():
    s = snapshot()
    trades = s.get("recent_trades", [])
    today = date.today().isoformat()

    todays = [t for t in trades if str(t.get("timestamp", "")).startswith(today)]
    buys = [t for t in todays if str(t.get("action", "")).upper() == "BUY"]
    sells = [t for t in todays if str(t.get("action", "")).upper() == "SELL"]

    net_today = 0
    wins = 0
    losses = 0

    for t in sells:
        try:
            pnl = float(t.get("pnl") or t.get("_pnl") or 0)
        except:
            pnl = 0
        net_today += pnl
        if pnl > 0:
            wins += 1
        else:
            losses += 1

    s["lab"] = {
        "today": today,
        "buys_today": len(buys),
        "sells_today": len(sells),
        "net_today": round(net_today, 2),
        "wins_today": wins,
        "losses_today": losses,
        "win_rate_today": round((wins / len(sells) * 100), 2) if sells else 0,
    }
    return s

@profit_lab_bp.route("/api/profit-lab")
def api_profit_lab():
    return jsonify(lab_snapshot())

@profit_lab_bp.route("/profit-lab")
def profit_lab():
    return render_template_string("""
<!doctype html>
<html>
<head>
<title>Ponder Profit Lab</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
:root{--border:#26334f;--muted:#a8b3c7;--green:#7cff9b;--red:#ff6f91;--blue:#8ab4ff;--yellow:#ffe86b}
body{margin:0;background:radial-gradient(circle at top left,#123322 0,#0b1024 35%,#050816 100%);color:white;font-family:Arial,sans-serif}
.wrap{max-width:1450px;margin:auto;padding:28px}
h1{font-size:40px;margin:0 0 8px}.ai{color:var(--green)}a{color:var(--blue);text-decoration:none}.muted{color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin:22px 0}
.card{background:linear-gradient(180deg,rgba(21,29,50,.96),rgba(11,17,34,.96));border:1px solid var(--border);border-radius:22px;padding:20px;box-shadow:0 15px 35px rgba(0,0,0,.25)}
.label{color:var(--muted);font-size:14px;font-weight:700}.value{font-size:30px;font-weight:900;margin-top:10px}
.good{color:var(--green)}.bad{color:var(--red)}.blue{color:var(--blue)}.yellow{color:var(--yellow)}
.layout{display:grid;grid-template-columns:2fr 1fr;gap:16px}.chartBox{height:390px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:10px;border-bottom:1px solid var(--border);text-align:left;white-space:nowrap}th{color:var(--blue)}
.scroll{overflow:auto}pre{white-space:pre-wrap;word-break:break-word;max-height:420px;overflow:auto;font-size:12px;line-height:1.4}
@media(max-width:900px){.layout{grid-template-columns:1fr}.wrap{padding:16px}h1{font-size:30px}}
</style>
</head>
<body>
<div class="wrap">
  <div style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap">
    <div>
      <h1>Ponder Invest <span class="ai">AI</span> Profit Lab</h1>
      <div class="muted">Experimental analytics page. Does not touch the stable Profit Ops dashboard.</div>
    </div>
    <div><a href="/">Main</a> · <a href="/profit">Profit Ops</a> · <a href="/profit-lab">Profit Lab</a></div>
  </div>

  <div class="grid">
    <div class="card"><div class="label">Today P/L</div><div class="value" id="todayPnl">$0</div><div class="muted" id="todayStats">0 buys · 0 sells</div></div>
    <div class="card"><div class="label">Today Win Rate</div><div class="value" id="todayWin">0%</div><div class="muted" id="todayWL">0 wins · 0 losses</div></div>
    <div class="card"><div class="label">AI Health</div><div class="value blue" id="health">--</div><div class="muted" id="healthNote">Waiting</div></div>
    <div class="card"><div class="label">Open P/L</div><div class="value" id="openPl">$0</div><div class="muted">Unrealized</div></div>
  </div>

  <div class="layout">
    <div class="card">
      <h2>Equity Lab Chart</h2>
      <div class="chartBox"><canvas id="chart"></canvas></div>
    </div>
    <div class="card">
      <h2>Bot Event Counts</h2>
      <table id="events"></table>
    </div>
  </div>

  <div class="card" style="margin-top:16px">
    <h2>Trade Replay Table</h2>
    <div class="scroll">
      <table>
        <thead><tr><th>Time</th><th>Action</th><th>Symbol</th><th>Qty</th><th>Price</th><th>P/L</th><th>P/L %</th><th>Score</th><th>Reason</th></tr></thead>
        <tbody id="replay"></tbody>
      </table>
    </div>
  </div>

  <div class="card" style="margin-top:16px">
    <h2>Decision Feed</h2>
    <pre id="feed"></pre>
  </div>
</div>

<script>
let chart=null;
function money(x){let n=Number(x||0);return "$"+n.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}
function pct(x){return Number(x||0).toFixed(2)+"%"}
function cls(x){return Number(x||0)>=0?"good":"bad"}

async function load(){
  let r=await fetch("/api/profit-lab",{cache:"no-store"});
  if(!r.ok)return;
  let d=await r.json();
  let l=d.latest||{}, lab=d.lab||{}, h=d.health||{}, logs=d.logs||{}, m=d.metrics||{};

  document.getElementById("todayPnl").textContent=money(lab.net_today);
  document.getElementById("todayPnl").className="value "+cls(lab.net_today);
  document.getElementById("todayStats").textContent=`${lab.buys_today||0} buys · ${lab.sells_today||0} sells`;
  document.getElementById("todayWin").textContent=pct(lab.win_rate_today);
  document.getElementById("todayWL").textContent=`${lab.wins_today||0} wins · ${lab.losses_today||0} losses`;
  document.getElementById("health").textContent=(h.score??"--")+"/100";
  document.getElementById("healthNote").textContent=h.note||"";
  document.getElementById("openPl").textContent=money(l.open_pl);
  document.getElementById("openPl").className="value "+cls(l.open_pl);

  let counts=logs.counts||{};
  document.getElementById("events").innerHTML="<tbody>"+Object.keys(counts).map(k=>`<tr><th>${k}</th><td>${counts[k]}</td></tr>`).join("")+"</tbody>";

  let eq=d.equity||[];
  let labels=eq.map(x=>x.timestamp);
  let data=[
    {label:"Portfolio Value",data:eq.map(x=>x.portfolio_value),tension:.35,pointRadius:2},
    {label:"Buying Power",data:eq.map(x=>x.buying_power),tension:.35,pointRadius:2},
    {label:"Open P/L",data:eq.map(x=>x.open_pl),tension:.35,pointRadius:2,yAxisID:"y1"}
  ];
  let opts={responsive:true,maintainAspectRatio:false,interaction:{mode:"index",intersect:false},scales:{x:{ticks:{maxTicksLimit:8}},y:{position:"left"},y1:{position:"right",grid:{drawOnChartArea:false}}}};
  if(!chart){chart=new Chart(document.getElementById("chart"),{type:"line",data:{labels:labels,datasets:data},options:opts})}
  else{chart.data.labels=labels;chart.data.datasets=data;chart.update()}

  document.getElementById("replay").innerHTML=(d.recent_trades||[]).map(t=>`<tr><td>${t.timestamp||""}</td><td>${t.action||""}</td><td>${t.symbol||""}</td><td>${t.qty||""}</td><td>${t.price||""}</td><td class="${cls(t.pnl||t._pnl)}">${t.pnl||t._pnl||""}</td><td class="${cls(t.pnl_pct||t._pnl_pct)}">${t.pnl_pct||t._pnl_pct||""}</td><td>${t.score||""}</td><td>${t.reason||""}</td></tr>`).join("") || "<tr><td colspan='9'>No replay rows yet.</td></tr>";
  document.getElementById("feed").textContent=(logs.decision_feed||[]).join("\\n") || "No recent decision logs.";
}
load();
setInterval(load,10000);
</script>
</body>
</html>
""")
''')

p = ROOT / "web_dashboard.py"
txt = p.read_text()

if "profit_lab_routes" not in txt:
    txt = "from profit_lab_routes import profit_lab_bp\n" + txt

if "register_blueprint(profit_lab_bp)" not in txt:
    m = re.search(r"^(\s*app\s*=\s*Flask\(.*?\)\s*)$", txt, re.M)
    if m:
        txt = txt[:m.end()] + "\napp.register_blueprint(profit_lab_bp)" + txt[m.end():]
    else:
        print("WARNING: Could not auto-register Profit Lab blueprint.")

p.write_text(txt)

print("DONE: Profit Lab installed safely at /profit-lab")
print("NEXT:")
print("python3 -m py_compile web_dashboard.py profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
