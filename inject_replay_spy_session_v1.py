from pathlib import Path
from datetime import datetime, date
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_replay_spy_session_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_ops_analytics.py")
backup("profit_ops_routes.py")

analytics = ROOT / "profit_ops_analytics.py"
txt = analytics.read_text()

# Add SPY/yfinance import safely
if "import yfinance as yf" not in txt:
    txt = txt.replace("import csv, os", "import csv, os\nimport yfinance as yf")

# Add helper functions before snapshot()
if "def session_stats(" not in txt:
    txt = txt.replace(
        "def snapshot():",
        r'''
def session_stats(trades):
    today = date.today().isoformat()
    todays = [t for t in trades if str(t.get("timestamp","")).startswith(today)]
    sells = [t for t in todays if str(t.get("action","")).upper()=="SELL"]
    buys = [t for t in todays if str(t.get("action","")).upper()=="BUY"]
    wins = [t for t in sells if t.get("_pnl",0) > 0]
    losses = [t for t in sells if t.get("_pnl",0) <= 0]
    net = sum(t.get("_pnl",0) for t in sells)
    return {
        "date": today,
        "buys_today": len(buys),
        "sells_today": len(sells),
        "closed_today": len(sells),
        "wins_today": len(wins),
        "losses_today": len(losses),
        "win_rate_today": round((len(wins)/len(sells)*100),2) if sells else 0,
        "net_pnl_today": round(net,2)
    }

def trade_replay(trades):
    rows = []
    ordered = list(trades)[-100:]
    for i,t in enumerate(reversed(ordered[-50:])):
        rows.append({
            "id": i,
            "timestamp": t.get("timestamp",""),
            "action": t.get("action",""),
            "symbol": t.get("symbol",""),
            "qty": t.get("qty",""),
            "price": t.get("price",""),
            "pnl": t.get("pnl", t.get("_pnl", "")),
            "pnl_pct": t.get("pnl_pct", t.get("_pnl_pct", "")),
            "score": t.get("score",""),
            "reason": t.get("reason",""),
        })
    return rows

def spy_benchmark(equity):
    if not equity:
        return []
    try:
        start = str(equity[0].get("timestamp",""))[:10]
        end = str(equity[-1].get("timestamp",""))[:10]
        if not start or start == "-":
            return []
        hist = yf.download("SPY", start=start, progress=False, auto_adjust=True)
        if hist is None or hist.empty:
            return []
        first = float(hist["Close"].iloc[0])
        last_known = first
        out = []
        for r in equity:
            ts = str(r.get("timestamp",""))
            day = ts[:10]
            try:
                if day in hist.index.strftime("%Y-%m-%d"):
                    last_known = float(hist.loc[hist.index.strftime("%Y-%m-%d") == day]["Close"].iloc[-1])
            except Exception:
                pass
            out.append({
                "timestamp": ts,
                "spy_index": round((last_known / first) * float(equity[0].get("portfolio_value", 1)), 2)
            })
        return out
    except Exception:
        return []

def snapshot():'''
    )

# Add fields inside return dict
if '"session":' not in txt:
    txt = txt.replace(
        '"recent_logs":raw_logs[-150:]',
        '''"recent_logs":raw_logs[-150:],
        "session": session_stats(trades),
        "replay": trade_replay(trades),
        "spy": spy_benchmark(eq)'''
    )

analytics.write_text(txt)

routes = ROOT / "profit_ops_routes.py"
rtxt = routes.read_text()

# Add cards
if "Session Today" not in rtxt:
    rtxt = rtxt.replace(
        '<div class="grid">',
        '''<div class="grid">
 <div class="card"><div class="label">Session Today</div><div class="value" id="sessionPnl">$0</div><div class="muted" id="sessionStats">0 buys · 0 sells</div></div>
 <div class="card"><div class="label">Today Win Rate</div><div class="value" id="sessionWinRate">0%</div><div class="muted" id="sessionWL">0 wins · 0 losses</div></div>
 <div class="card"><div class="label">Benchmark</div><div class="value blue">SPY</div><div class="muted">Equity curve comparison</div></div>'''
    )

# Add replay section before recent logs
if "Trade Replay" not in rtxt:
    rtxt = rtxt.replace(
        '<div class="card" style="margin-top:16px"><h2 class="sectionTitle">Recent Bot Logs</h2><pre id="recentLogs"></pre></div>',
        '''<div class="card" style="margin-top:16px"><h2 class="sectionTitle">Trade Replay</h2><div class="scroll"><table><thead><tr><th>Time</th><th>Action</th><th>Symbol</th><th>Qty</th><th>Price</th><th>P/L</th><th>P/L %</th><th>Score</th><th>Reason</th></tr></thead><tbody id="replayRows"></tbody></table></div></div>
<div class="card" style="margin-top:16px"><h2 class="sectionTitle">Recent Bot Logs</h2><pre id="recentLogs"></pre></div>'''
    )

# Add SPY dataset
if 'label:"SPY Benchmark"' not in rtxt:
    rtxt = rtxt.replace(
        '{label:"Open P/L",data:eq.map(x=>x.open_pl),tension:.35,pointRadius:2,yAxisID:"y1"}',
        '{label:"Open P/L",data:eq.map(x=>x.open_pl),tension:.35,pointRadius:2,yAxisID:"y1"},\n  {label:"SPY Benchmark",data:(d.spy||[]).map(x=>x.spy_index),tension:.35,pointRadius:1}'
    )

# Add session/replay JS
if "sessionPnl" in rtxt and "let s=d.session" not in rtxt:
    rtxt = rtxt.replace(
        'let d=await r.json(),l=d.latest||{},m=d.metrics||{},h=d.health||{},logs=d.logs||{},ui=d.ui||{};',
        'let d=await r.json(),l=d.latest||{},m=d.metrics||{},h=d.health||{},logs=d.logs||{},ui=d.ui||{},s=d.session||{};'
    )
    rtxt = rtxt.replace(
        'document.getElementById("portfolio").textContent=money(l.portfolio_value);',
        '''if(document.getElementById("sessionPnl")){
   document.getElementById("sessionPnl").textContent=money(s.net_pnl_today||0);
   document.getElementById("sessionPnl").className="value "+cls(s.net_pnl_today||0);
   document.getElementById("sessionStats").textContent=`${s.buys_today||0} buys · ${s.sells_today||0} sells`;
   document.getElementById("sessionWinRate").textContent=pct(s.win_rate_today||0);
   document.getElementById("sessionWL").textContent=`${s.wins_today||0} wins · ${s.losses_today||0} losses`;
 }
 document.getElementById("portfolio").textContent=money(l.portfolio_value);'''
    )
    rtxt = rtxt.replace(
        'document.getElementById("recentLogs").textContent=(d.recent_logs||[]).join("\\n");',
        '''if(document.getElementById("replayRows")){
   document.getElementById("replayRows").innerHTML=(d.replay||[]).map(t=>`<tr><td>${t.timestamp||""}</td><td>${t.action||""}</td><td>${t.symbol||""}</td><td>${t.qty||""}</td><td>${t.price||""}</td><td class="${cls(t.pnl)}">${t.pnl||""}</td><td class="${cls(t.pnl_pct)}">${t.pnl_pct||""}</td><td>${t.score||""}</td><td>${t.reason||""}</td></tr>`).join("") || "<tr><td colspan='9'>No replay rows yet.</td></tr>";
 }
 document.getElementById("recentLogs").textContent=(d.recent_logs||[]).join("\\n");'''
    )

routes.write_text(rtxt)

print("DONE: Replay + SPY + Session Stats installed")
print("NEXT:")
print("python3 -m py_compile profit_ops_analytics.py profit_ops_routes.py")
print("sudo systemctl restart tradebot-dashboard")
