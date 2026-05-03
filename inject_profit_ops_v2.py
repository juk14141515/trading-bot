from pathlib import Path
from datetime import datetime
import shutil, re

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_profit_ops_v2_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("web_dashboard.py")
backup("profit_ops_analytics.py")
backup("profit_ops_routes.py")

# ========================
# ANALYTICS ENGINE
# ========================
(ROOT / "profit_ops_analytics.py").write_text('''
import csv, os
from collections import defaultdict, Counter
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRADE_FILE = os.path.join(BASE_DIR, "trade_history.csv")
EQUITY_FILE = os.path.join(BASE_DIR, "equity_history.csv")
LOG_FILE = os.path.join(BASE_DIR, "log.txt")

def f(x):
    try: return float(x)
    except: return 0

def read_equity():
    rows=[]
    if not os.path.exists(EQUITY_FILE): return rows
    with open(EQUITY_FILE) as fobj:
        for r in csv.DictReader(fobj):
            rows.append({
                "timestamp": r.get("timestamp",""),
                "portfolio_value": f(r.get("portfolio_value")),
                "buying_power": f(r.get("buying_power")),
                "open_pl": f(r.get("open_pl")),
            })
    return rows[-500:]

def read_trades():
    rows=[]
    if not os.path.exists(TRADE_FILE): return rows
    with open(TRADE_FILE) as fobj:
        for r in csv.DictReader(fobj):
            r["_pnl"]=f(r.get("pnl"))
            r["_pnl_pct"]=f(r.get("pnl_pct"))
            rows.append(r)
    return rows[-500:]

def drawdown(eq):
    vals=[x["portfolio_value"] for x in eq if x.get("portfolio_value")]
    if not vals: return 0
    peak=vals[0]; maxdd=0
    for v in vals:
        if v>peak: peak=v
        dd=(peak-v)/peak if peak else 0
        if dd>maxdd: maxdd=dd
    return round(maxdd*100,2)

def metrics(trades):
    sells=[t for t in trades if str(t.get("action")).upper()=="SELL"]
    wins=[t for t in sells if t["_pnl"]>0]
    losses=[t for t in sells if t["_pnl"]<=0]

    total=sum(t["_pnl"] for t in sells)
    winrate=(len(wins)/len(sells)*100) if sells else 0

    bysym=defaultdict(float)
    for t in sells:
        bysym[t.get("symbol","UNK")]+=t["_pnl"]

    best=max(bysym,key=bysym.get) if bysym else "-"
    worst=min(bysym,key=bysym.get) if bysym else "-"

    return {
        "win_rate": round(winrate,2),
        "net_pnl": round(total,2),
        "wins": len(wins),
        "losses": len(losses),
        "best": best,
        "worst": worst
    }

def snapshot():
    eq=read_equity()
    tr=read_trades()
    m=metrics(tr)
    return {
        "latest": eq[-1] if eq else {},
        "equity": eq,
        "metrics": m,
        "drawdown": drawdown(eq),
        "trades": tr[-50:]
    }
''')

# ========================
# DASHBOARD UI
# ========================
(ROOT / "profit_ops_routes.py").write_text('''
from flask import Blueprint, jsonify, render_template_string
from profit_ops_analytics import snapshot

bp = Blueprint("profit_ops", __name__)

@bp.route("/api/profit-ops")
def api():
    return jsonify(snapshot())

@bp.route("/profit")
def profit():
    return render_template_string("""
<html>
<head>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body{background:#0f172a;color:white;font-family:sans-serif;padding:20px}
.card{background:#111827;padding:15px;border-radius:12px;margin:10px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px}
</style>
</head>
<body>
<h1>Ponder Profit Ops 🚀</h1>

<div class="grid">
<div class="card">Portfolio: <span id="p"></span></div>
<div class="card">Open PnL: <span id="pl"></span></div>
<div class="card">Win Rate: <span id="wr"></span></div>
<div class="card">Net PnL: <span id="np"></span></div>
<div class="card">Drawdown: <span id="dd"></span></div>
</div>

<canvas id="chart" height="120"></canvas>

<script>
let c;

async function load(){
 let r=await fetch("/api/profit-ops");
 let d=await r.json();

 document.getElementById("p").innerText=d.latest.portfolio_value;
 document.getElementById("pl").innerText=d.latest.open_pl;
 document.getElementById("wr").innerText=d.metrics.win_rate+"%";
 document.getElementById("np").innerText=d.metrics.net_pnl;
 document.getElementById("dd").innerText=d.drawdown+"%";

 let labels=d.equity.map(x=>x.timestamp);
 let vals=d.equity.map(x=>x.portfolio_value);

 if(!c){
  c=new Chart(document.getElementById("chart"),{
   type:"line",
   data:{labels:labels,datasets:[{label:"Equity",data:vals}]}
  });
 }else{
  c.data.labels=labels;
  c.data.datasets[0].data=vals;
  c.update();
 }
}

load();
setInterval(load,5000);
</script>
</body>
</html>
""")
''')

# ========================
# PATCH DASHBOARD
# ========================
p = ROOT / "web_dashboard.py"
txt = p.read_text()

if "profit_ops_routes" not in txt:
    txt = "from profit_ops_routes import bp as profit_ops_bp\n" + txt

if "register_blueprint" not in txt:
    txt = txt.replace("Flask(__name__)", "Flask(__name__)\napp.register_blueprint(profit_ops_bp)")

p.write_text(txt)

print("✅ Profit Ops V2 installed")
