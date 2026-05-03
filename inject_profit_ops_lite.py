from pathlib import Path
from datetime import datetime
import re, shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_profit_ops_lite_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("web_dashboard.py")
backup("bot.py")

# -----------------------------
# 1. Analytics module
# -----------------------------
(ROOT / "profit_ops_analytics.py").write_text('''
import csv, os
from collections import defaultdict
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRADE_FILE = os.path.join(BASE_DIR, "trade_history.csv")
EQUITY_FILE = os.path.join(BASE_DIR, "equity_history.csv")
LOG_FILE = os.path.join(BASE_DIR, "log.txt")

def f(x):
    try: return float(x)
    except: return 0.0

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

def drawdown(eq):
    vals=[x["portfolio_value"] for x in eq if x.get("portfolio_value")]
    if not vals: return 0
    peak=vals[0]; maxdd=0
    for v in vals:
        if v>peak: peak=v
        dd=(peak-v)/peak if peak else 0
        if dd>maxdd: maxdd=dd
    return round(maxdd*100,2)

def read_trades():
    rows=[]
    if not os.path.exists(TRADE_FILE): return rows
    with open(TRADE_FILE) as fobj:
        for r in csv.DictReader(fobj):
            r["_pnl"]=f(r.get("pnl"))
            r["_pnl_pct"]=f(r.get("pnl_pct"))
            rows.append(r)
    return rows[-500:]

def metrics():
    trades=read_trades()
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
    m=metrics()
    return {
        "latest": eq[-1] if eq else {},
        "equity": eq,
        "metrics": m,
        "drawdown": drawdown(eq),
        "trades": tr[-50:]
    }
''')

# -----------------------------
# 2. Dashboard route
# -----------------------------
(ROOT / "profit_ops_routes.py").write_text('''
from flask import Blueprint, jsonify, render_template_string
from profit_ops_analytics import snapshot

bp = Blueprint("profit_ops", __name__)

@bp.route("/profit")
def profit():
    data = snapshot()
    html = f"""
    <html><body style='background:#0f172a;color:white;font-family:sans-serif'>
    <h1>Ponder Profit Ops 🐾</h1>
    <p>Portfolio: {data["latest"].get("portfolio_value","-")}</p>
    <p>Open PnL: {data["latest"].get("open_pl","-")}</p>
    <p>Win Rate: {data["metrics"]["win_rate"]}%</p>
    <p>Net PnL: {data["metrics"]["net_pnl"]}</p>
    <p>Drawdown: {data["drawdown"]}%</p>
    <h2>Recent Trades</h2>
    <pre>{data["trades"]}</pre>
    </body></html>
    """
    return render_template_string(html)
''')

# -----------------------------
# 3. Patch dashboard
# -----------------------------
p = ROOT / "web_dashboard.py"
txt = p.read_text()

if "profit_ops_routes" not in txt:
    txt = "from profit_ops_routes import bp as profit_ops_bp\n" + txt

if "register_blueprint" not in txt:
    txt = txt.replace("Flask(__name__)", "Flask(__name__)\napp.register_blueprint(profit_ops_bp)")

p.write_text(txt)

print("DONE: Profit Ops Lite installed")
