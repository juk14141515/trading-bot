from pathlib import Path
from datetime import datetime
import shutil, re

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_profit_ops_v3_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("web_dashboard.py")
backup("profit_ops_analytics.py")
backup("profit_ops_routes.py")

(ROOT / "profit_ops_analytics.py").write_text(r'''
import csv, os
from collections import defaultdict, Counter
from datetime import datetime

BASE_DIR=os.path.dirname(os.path.abspath(__file__))
TRADE_FILE=os.path.join(BASE_DIR,"trade_history.csv")
EQUITY_FILE=os.path.join(BASE_DIR,"equity_history.csv")
LOG_FILE=os.path.join(BASE_DIR,"log.txt")

def sf(x):
    try: return float(x)
    except: return 0.0

def read_equity(limit=1000):
    rows=[]
    if not os.path.exists(EQUITY_FILE): return rows
    try:
        with open(EQUITY_FILE,newline="",errors="ignore") as f:
            for r in csv.DictReader(f):
                rows.append({
                    "timestamp":r.get("timestamp",""),
                    "portfolio_value":sf(r.get("portfolio_value")),
                    "buying_power":sf(r.get("buying_power")),
                    "open_pl":sf(r.get("open_pl")),
                })
    except Exception:
        return []
    return rows[-limit:]

def read_trades(limit=1000):
    rows=[]
    if not os.path.exists(TRADE_FILE): return rows
    try:
        with open(TRADE_FILE,newline="",errors="ignore") as f:
            for r in csv.DictReader(f):
                r["_pnl"]=sf(r.get("pnl"))
                r["_pnl_pct"]=sf(r.get("pnl_pct"))
                r["_qty"]=sf(r.get("qty"))
                r["_price"]=sf(r.get("price"))
                r["_score"]=sf(r.get("score"))
                rows.append(r)
    except Exception:
        return []
    return rows[-limit:]

def read_logs(limit=400):
    if not os.path.exists(LOG_FILE): return []
    try:
        with open(LOG_FILE,"r",errors="ignore") as f:
            return [x.rstrip() for x in f.readlines()[-limit:]]
    except Exception:
        return []

def max_drawdown(eq):
    vals=[r["portfolio_value"] for r in eq if r.get("portfolio_value")]
    if not vals: return 0
    peak=vals[0]; maxdd=0
    for v in vals:
        peak=max(peak,v)
        if peak:
            maxdd=max(maxdd,(peak-v)/peak)
    return round(maxdd*100,2)

def equity_change(eq):
    vals=[r["portfolio_value"] for r in eq if r.get("portfolio_value")]
    if len(vals)<2: return {"dollar":0,"pct":0}
    d=vals[-1]-vals[0]
    p=(d/vals[0]*100) if vals[0] else 0
    return {"dollar":round(d,2),"pct":round(p,2)}

def trade_metrics(trades):
    sells=[t for t in trades if str(t.get("action","")).upper()=="SELL"]
    buys=[t for t in trades if str(t.get("action","")).upper()=="BUY"]
    wins=[t for t in sells if t["_pnl"]>0]
    losses=[t for t in sells if t["_pnl"]<=0]

    net=sum(t["_pnl"] for t in sells)
    gross_win=sum(t["_pnl"] for t in wins)
    gross_loss=abs(sum(t["_pnl"] for t in losses))
    pf=(gross_win/gross_loss) if gross_loss else (gross_win if gross_win else 0)

    bysym=defaultdict(float)
    sym_counts=Counter()
    sym_wins=Counter()
    sym_losses=Counter()
    reasons=Counter()

    for t in sells:
        sym=t.get("symbol","UNK")
        bysym[sym]+=t["_pnl"]
        sym_counts[sym]+=1
        if t["_pnl"]>0: sym_wins[sym]+=1
        else: sym_losses[sym]+=1
        reasons[t.get("reason","unknown") or "unknown"]+=1

    best=max(bysym,key=bysym.get) if bysym else "-"
    worst=min(bysym,key=bysym.get) if bysym else "-"

    symbol_rows=[]
    for sym,pnl in sorted(bysym.items(),key=lambda x:x[1],reverse=True):
        total=sym_counts[sym]
        wr=round((sym_wins[sym]/total*100),2) if total else 0
        symbol_rows.append({
            "symbol":sym,
            "pnl":round(pnl,2),
            "trades":total,
            "wins":sym_wins[sym],
            "losses":sym_losses[sym],
            "win_rate":wr
        })

    return {
        "total_trades":len(trades),
        "buys":len(buys),
        "closed_trades":len(sells),
        "wins":len(wins),
        "losses":len(losses),
        "win_rate":round((len(wins)/len(sells)*100),2) if sells else 0,
        "net_closed_pnl":round(net,2),
        "avg_win":round(gross_win/len(wins),2) if wins else 0,
        "avg_loss":round(-gross_loss/len(losses),2) if losses else 0,
        "profit_factor":round(pf,2),
        "best_symbol":best,
        "best_symbol_pnl":round(bysym.get(best,0),2) if best!="-" else 0,
        "worst_symbol":worst,
        "worst_symbol_pnl":round(bysym.get(worst,0),2) if worst!="-" else 0,
        "symbol_rows":symbol_rows[:20],
        "exit_reasons":[{"reason":k,"count":v} for k,v in reasons.most_common(12)]
    }

def log_intelligence(logs):
    keys=["SCANNER","ADAPTIVE","CONFIDENCE","BUY DECISION","SKIP BUY","ROTATION","SELL","BUY","ERROR","WEAK POSITION"]
    counts={k:0 for k in keys}
    decision=[]; warnings=[]
    for line in logs:
        for k in keys:
            if k in line: counts[k]+=1
        if any(x in line for x in ["CONFIDENCE","BUY DECISION","SKIP BUY","SCANNER"]):
            decision.append(line)
        if any(x in line for x in ["ERROR","STOP_TRADING","EMERGENCY","Traceback"]):
            warnings.append(line)
    return {"counts":counts,"decision_feed":decision[-100:],"warnings":warnings[-30:]}

def health_score(latest,metrics,dd,logs):
    score=100.0
    open_pl=sf(latest.get("open_pl"))
    if open_pl<0: score-=min(25,abs(open_pl)/20)
    if dd>1: score-=min(25,dd*4)
    if metrics["closed_trades"]>=5 and metrics["win_rate"]<45: score-=20
    if metrics["closed_trades"]>=5 and metrics["net_closed_pnl"]<0: score-=20
    if logs["counts"].get("ERROR",0)>0: score-=15
    if logs["counts"].get("SCANNER",0)==0: score-=10

    score=round(max(0,min(100,score)),1)
    if metrics["closed_trades"]<5:
        note="Learning mode: not enough closed trades yet."
    elif score>=75:
        note="Healthy: risk and performance look stable."
    elif score>=50:
        note="Caution: monitor drawdown, exits, and scanner flow."
    else:
        note="Defensive: review weak trades before increasing risk."
    return {"score":score,"note":note}

def snapshot():
    eq=read_equity()
    trades=read_trades()
    raw_logs=read_logs()
    latest=eq[-1] if eq else {"timestamp":"-","portfolio_value":0,"buying_power":0,"open_pl":0}
    metrics=trade_metrics(trades)
    dd=max_drawdown(eq)
    logs=log_intelligence(raw_logs)
    return {
        "generated_at":datetime.now().isoformat(timespec="seconds"),
        "latest":latest,
        "equity":eq,
        "equity_change":equity_change(eq),
        "metrics":metrics,
        "drawdown":dd,
        "logs":logs,
        "health":health_score(latest,metrics,dd,logs),
        "recent_trades":list(reversed(trades[-75:])),
        "recent_logs":raw_logs[-150:]
    }
''')

(ROOT / "profit_ops_routes.py").write_text(r'''
from flask import Blueprint, jsonify, render_template_string
from profit_ops_analytics import snapshot

bp=Blueprint("profit_ops",__name__)

@bp.route("/api/profit-ops")
def api_profit_ops():
    return jsonify(snapshot())

@bp.route("/profit")
@bp.route("/profit/history")
def profit():
    return render_template_string("""
<!doctype html>
<html>
<head>
<title>Ponder Invest AI | Profit Ops</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
:root{--bg:#070b18;--card:#111827;--card2:#151d32;--border:#26334f;--text:#f8fafc;--muted:#a8b3c7;--green:#7cff9b;--red:#ff6f91;--blue:#8ab4ff;--yellow:#ffe86b}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at top left,#123322 0,#0b1024 35%,#050816 100%);color:var(--text);font-family:Arial,sans-serif}
.wrap{max-width:1480px;margin:auto;padding:28px}
.top{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;align-items:flex-start}
h1{font-size:40px;margin:0 0 8px}.ai{color:var(--green)}
a{color:var(--blue);text-decoration:none}.muted{color:var(--muted)}
.pill{display:inline-block;border:1px solid var(--border);background:rgba(255,255,255,.08);border-radius:999px;padding:9px 14px;margin:7px 6px 0 0;font-weight:800}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:16px;margin:22px 0}
.card{background:linear-gradient(180deg,rgba(21,29,50,.96),rgba(11,17,34,.96));border:1px solid var(--border);border-radius:22px;padding:20px;box-shadow:0 15px 35px rgba(0,0,0,.25)}
.label{color:var(--muted);font-size:14px;font-weight:700}.value{font-size:30px;font-weight:900;margin-top:10px}
.good{color:var(--green)}.bad{color:var(--red)}.blue{color:var(--blue)}.yellow{color:var(--yellow)}
.layout{display:grid;grid-template-columns:2fr 1fr;gap:16px}.layout2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.chartBox{height:390px}.miniChart{height:270px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:10px;border-bottom:1px solid var(--border);text-align:left;white-space:nowrap}th{color:var(--blue)}
.scroll{overflow:auto}pre{white-space:pre-wrap;word-break:break-word;max-height:460px;overflow:auto;font-size:12px;line-height:1.4;color:#d7def0}
.sectionTitle{margin:0 0 14px;font-size:21px}
.barWrap{height:14px;background:#0b1225;border-radius:999px;overflow:hidden;border:1px solid var(--border)}.bar{height:100%;background:linear-gradient(90deg,var(--red),var(--yellow),var(--green));width:0%}
@media(max-width:900px){.layout,.layout2{grid-template-columns:1fr}.wrap{padding:16px}h1{font-size:30px}}
</style>
</head>
<body>
<div class="wrap">
<div class="top">
 <div>
  <h1>Ponder Invest <span class="ai">AI</span> Profit Ops</h1>
  <div class="muted">Performance, AI decision feed, trade breakdown, exit reasons, and health score.</div>
  <div><span class="pill">LIVE</span><span class="pill" id="healthPill">Health: --</span><span class="pill" id="updated">Updated: --</span></div>
 </div>
 <div><a href="/">Main Dashboard</a> · <a href="/profit">Profit Ops</a> · <a href="/history">History</a> · <a href="/logout">Logout</a></div>
</div>

<div class="grid">
 <div class="card"><div class="label">Portfolio Value</div><div class="value" id="portfolio">$0</div><div class="muted" id="equityChange">$0 / 0%</div></div>
 <div class="card"><div class="label">Buying Power</div><div class="value" id="buyingPower">$0</div><div class="muted">Available capital</div></div>
 <div class="card"><div class="label">Open P/L</div><div class="value" id="openPl">$0</div><div class="muted">Unrealized</div></div>
 <div class="card"><div class="label">Max Drawdown</div><div class="value" id="drawdown">0%</div><div class="muted">From equity history</div></div>
 <div class="card"><div class="label">Closed Win Rate</div><div class="value" id="winRate">0%</div><div class="muted" id="winsLosses">0 wins · 0 losses</div></div>
 <div class="card"><div class="label">Closed Net P/L</div><div class="value" id="netPnl">$0</div><div class="muted" id="closedTrades">0 closed trades</div></div>
 <div class="card"><div class="label">Profit Factor</div><div class="value" id="profitFactor">0.00</div><div class="muted">Gross wins / losses</div></div>
 <div class="card"><div class="label">Best / Worst</div><div class="value blue" id="bestWorst">- / -</div><div class="muted" id="bestWorstPnl">$0 / $0</div></div>
</div>

<div class="layout">
 <div class="card"><h2 class="sectionTitle">Equity Curve</h2><div class="chartBox"><canvas id="equityChart"></canvas></div></div>
 <div class="card"><h2 class="sectionTitle">AI Health Score</h2><div class="value" id="healthScore">--</div><div class="barWrap"><div class="bar" id="healthBar"></div></div><p class="muted" id="healthNote"></p><h2 class="sectionTitle">Event Counts</h2><table id="eventTable"></table></div>
</div>

<div class="layout2" style="margin-top:16px">
 <div class="card"><h2 class="sectionTitle">Trade Breakdown by Symbol</h2><div class="miniChart"><canvas id="symbolChart"></canvas></div><div class="scroll"><table><thead><tr><th>Symbol</th><th>P/L</th><th>Trades</th><th>Wins</th><th>Losses</th><th>Win Rate</th></tr></thead><tbody id="symbolRows"></tbody></table></div></div>
 <div class="card"><h2 class="sectionTitle">Exit Reason Tracking</h2><div class="miniChart"><canvas id="reasonChart"></canvas></div><table id="reasonRows"></table></div>
</div>

<div class="card" style="margin-top:16px"><h2 class="sectionTitle">Recent Trade Journal</h2><div class="scroll"><table><thead><tr><th>Time</th><th>Action</th><th>Symbol</th><th>Qty</th><th>Price</th><th>P/L</th><th>P/L %</th><th>Score</th><th>Reason</th></tr></thead><tbody id="tradeRows"></tbody></table></div></div>

<div class="layout2" style="margin-top:16px">
 <div class="card"><h2 class="sectionTitle">Live Decision Feed</h2><pre id="decisionFeed"></pre></div>
 <div class="card"><h2 class="sectionTitle">Warnings / Errors</h2><pre id="warnings"></pre></div>
</div>

<div class="card" style="margin-top:16px"><h2 class="sectionTitle">Recent Bot Logs</h2><pre id="recentLogs"></pre></div>
</div>

<script>
let equityChart=null,symbolChart=null,reasonChart=null;
function money(x){let n=Number(x||0);return "$"+n.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}
function pct(x){return Number(x||0).toFixed(2)+"%"}
function cls(x){return Number(x||0)>=0?"good":"bad"}
function setClass(id,base,x){let e=document.getElementById(id);e.className=base+" "+cls(x)}
function chart(obj,id,type,labels,datasets,options={}){
 if(!obj){return new Chart(document.getElementById(id),{type:type,data:{labels:labels,datasets:datasets},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:"index",intersect:false},...options}})}
 obj.data.labels=labels;obj.data.datasets=datasets;obj.update();return obj;
}
async function load(){
 let r=await fetch("/api/profit-ops",{cache:"no-store"}); if(!r.ok)return;
 let d=await r.json(),l=d.latest||{},m=d.metrics||{},h=d.health||{},logs=d.logs||{};
 document.getElementById("updated").textContent="Updated: "+(d.generated_at||"--");
 document.getElementById("portfolio").textContent=money(l.portfolio_value);
 document.getElementById("buyingPower").textContent=money(l.buying_power);
 document.getElementById("openPl").textContent=money(l.open_pl);setClass("openPl","value",l.open_pl);
 document.getElementById("drawdown").textContent=pct(d.drawdown);
 document.getElementById("winRate").textContent=pct(m.win_rate);
 document.getElementById("winsLosses").textContent=`${m.wins||0} wins · ${m.losses||0} losses`;
 document.getElementById("netPnl").textContent=money(m.net_closed_pnl);setClass("netPnl","value",m.net_closed_pnl);
 document.getElementById("closedTrades").textContent=`${m.closed_trades||0} closed trades · ${m.buys||0} buys`;
 document.getElementById("profitFactor").textContent=Number(m.profit_factor||0).toFixed(2);
 document.getElementById("bestWorst").textContent=`${m.best_symbol||"-"} / ${m.worst_symbol||"-"}`;
 document.getElementById("bestWorstPnl").textContent=`${money(m.best_symbol_pnl)} / ${money(m.worst_symbol_pnl)}`;
 document.getElementById("equityChange").textContent=`${money((d.equity_change||{}).dollar)} / ${pct((d.equity_change||{}).pct)}`;
 document.getElementById("healthScore").textContent=(h.score??"--")+"/100";
 document.getElementById("healthPill").textContent="AI Health: "+(h.score??"--")+"/100";
 document.getElementById("healthNote").textContent=h.note||"";
 document.getElementById("healthBar").style.width=(h.score||0)+"%";

 let counts=logs.counts||{};
 document.getElementById("eventTable").innerHTML="<tbody>"+Object.keys(counts).map(k=>`<tr><th>${k}</th><td>${counts[k]}</td></tr>`).join("")+"</tbody>";

 let eq=d.equity||[];
 equityChart=chart(equityChart,"equityChart","line",eq.map(x=>x.timestamp),[
  {label:"Portfolio Value",data:eq.map(x=>x.portfolio_value),tension:.25},
  {label:"Buying Power",data:eq.map(x=>x.buying_power),tension:.25},
  {label:"Open P/L",data:eq.map(x=>x.open_pl),tension:.25,yAxisID:"y1"}
 ],{scales:{x:{ticks:{maxTicksLimit:8}},y:{position:"left"},y1:{position:"right",grid:{drawOnChartArea:false}}}});

 let syms=m.symbol_rows||[];
 symbolChart=chart(symbolChart,"symbolChart","bar",syms.map(x=>x.symbol),[{label:"Closed P/L",data:syms.map(x=>x.pnl)}]);
 document.getElementById("symbolRows").innerHTML=syms.map(x=>`<tr><td>${x.symbol}</td><td class="${cls(x.pnl)}">${money(x.pnl)}</td><td>${x.trades}</td><td>${x.wins}</td><td>${x.losses}</td><td>${pct(x.win_rate)}</td></tr>`).join("") || "<tr><td colspan='6'>No closed trades yet.</td></tr>";

 let reasons=m.exit_reasons||[];
 reasonChart=chart(reasonChart,"reasonChart","bar",reasons.map(x=>x.reason),[{label:"Exit Count",data:reasons.map(x=>x.count)}],{indexAxis:"y"});
 document.getElementById("reasonRows").innerHTML="<tbody>"+(reasons.map(x=>`<tr><th>${x.reason}</th><td>${x.count}</td></tr>`).join("") || "<tr><td>No exits yet.</td></tr>")+"</tbody>";

 document.getElementById("tradeRows").innerHTML=(d.recent_trades||[]).map(t=>`<tr><td>${t.timestamp||""}</td><td>${t.action||""}</td><td>${t.symbol||""}</td><td>${t.qty||""}</td><td>${t.price||""}</td><td class="${cls(t.pnl||t._pnl)}">${t.pnl||t._pnl||""}</td><td class="${cls(t.pnl_pct||t._pnl_pct)}">${t.pnl_pct||t._pnl_pct||""}</td><td>${t.score||""}</td><td>${t.reason||""}</td></tr>`).join("") || "<tr><td colspan='9'>No trade journal rows yet.</td></tr>";

 document.getElementById("decisionFeed").textContent=(logs.decision_feed||[]).join("\\n") || "No recent confidence/scanner/buy-skip logs yet.";
 document.getElementById("warnings").textContent=(logs.warnings||[]).join("\\n") || "No recent warnings.";
 document.getElementById("recentLogs").textContent=(d.recent_logs||[]).join("\\n");
}
load();setInterval(load,10000);
</script>
</body>
</html>
""")
''')

p=ROOT/"web_dashboard.py"
txt=p.read_text()

if "profit_ops_routes" not in txt:
    txt="from profit_ops_routes import bp as profit_ops_bp\n"+txt

if "register_blueprint(profit_ops_bp)" not in txt:
    m=re.search(r"^(\s*app\s*=\s*Flask\(.*?\)\s*)$",txt,re.M)
    if m:
        txt=txt[:m.end()]+"\napp.register_blueprint(profit_ops_bp)"+txt[m.end():]
    else:
        print("WARNING: could not auto-register blueprint; /profit may already be registered.")

if "ponder_ai_health_badge" not in txt:
    txt += r'''

@app.after_request
def ponder_ai_health_badge(response):
    try:
        if not response.content_type.startswith("text/html"):
            return response
        body=response.get_data(as_text=True)
        if "</body>" not in body:
            return response
        from profit_ops_analytics import snapshot
        s=snapshot()
        h=s.get("health",{}).get("score","--")
        open_pl=s.get("latest",{}).get("open_pl",0)
        color="#7cff9b" if float(open_pl or 0)>=0 else "#ff6f91"
        badge=f"""
        <div id='ponder_ai_health_badge' style='position:fixed;right:18px;bottom:18px;z-index:9999;background:#111827;border:1px solid #26334f;border-radius:18px;padding:12px 14px;color:white;font-family:Arial;box-shadow:0 10px 30px rgba(0,0,0,.35)'>
          <div style='font-weight:900'>AI Health: {h}/100</div>
          <div style='font-size:12px;color:#a8b3c7'>Open P/L: <span style='color:{color}'>${float(open_pl or 0):,.2f}</span></div>
          <div style='font-size:12px;margin-top:6px'><a href='/' style='color:#8ab4ff'>Dashboard</a> · <a href='/profit' style='color:#8ab4ff'>Profit Ops</a></div>
        </div>
        """
        body=body.replace("</body>",badge+"</body>")
        response.set_data(body)
    except Exception:
        pass
    return response
'''

p.write_text(txt)
print("DONE: Profit Ops V3 + main dashboard health/link badge installed")
print("NEXT:")
print("python3 -m py_compile web_dashboard.py profit_ops_analytics.py profit_ops_routes.py")
print("sudo systemctl restart tradebot-dashboard")
