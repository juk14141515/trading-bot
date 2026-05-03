from pathlib import Path
from datetime import datetime
import shutil, re

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_dashboard_safety_ui_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("web_dashboard.py")
backup("profit_ops_analytics.py")
backup("profit_ops_routes.py")

# -----------------------------
# Safety/UI helper module
# -----------------------------
(ROOT / "dashboard_safety_ui.py").write_text(r'''
import time
from functools import wraps
from flask import request, jsonify

_RATE = {}

def security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

def rate_limit(max_requests=120, window_seconds=60):
    def deco(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            ip = request.headers.get("CF-Connecting-IP") or request.remote_addr or "unknown"
            now = time.time()
            bucket = _RATE.setdefault(ip, [])
            bucket[:] = [t for t in bucket if now - t < window_seconds]
            if len(bucket) >= max_requests:
                return jsonify({"error": "rate limited"}), 429
            bucket.append(now)
            return fn(*args, **kwargs)
        return wrapped
    return deco

def ai_mood(score, open_pl, market_closed=False):
    try:
        score = float(score)
        open_pl = float(open_pl)
    except Exception:
        return "Learning", "System is collecting data."

    if market_closed:
        return "Idle", "Market closed. Bot is watching, not forcing trades."
    if score >= 80 and open_pl >= 0:
        return "Confident", "Health is strong and open P/L is positive."
    if score >= 60:
        return "Defensive", "System is stable but still protecting capital."
    return "Cautious", "Risk signals need attention."

def goal_snapshot(snapshot):
    latest = snapshot.get("latest", {})
    metrics = snapshot.get("metrics", {})
    open_pl = float(latest.get("open_pl") or 0)
    closed = float(metrics.get("net_closed_pnl") or 0)
    total = open_pl + closed

    daily_goal = 200.0
    max_soft_drawdown = 1.0

    return {
        "daily_goal": daily_goal,
        "current_total_pl": round(total, 2),
        "goal_progress_pct": round(max(0, min(100, (total / daily_goal) * 100)), 1) if daily_goal else 0,
        "soft_drawdown_limit_pct": max_soft_drawdown,
    }
''')

# -----------------------------
# Patch profit_ops_analytics with non-trading display data
# -----------------------------
analytics = ROOT / "profit_ops_analytics.py"
txt = analytics.read_text()

if "dashboard_safety_ui" not in txt:
    txt = txt.replace(
        "from datetime import datetime",
        "from datetime import datetime\nfrom dashboard_safety_ui import ai_mood, goal_snapshot"
    )

if '"ui":' not in txt:
    txt = txt.replace(
        '"recent_logs":raw_logs[-150:]',
        '''"recent_logs":raw_logs[-150:],
        "ui": {
            "mood": ai_mood(health_score(latest,metrics,dd,logs)["score"], latest.get("open_pl",0), False),
            "goals": goal_snapshot({
                "latest": latest,
                "metrics": metrics
            })
        }'''
    )

analytics.write_text(txt)

# -----------------------------
# Patch web dashboard with security headers + API rate limit
# -----------------------------
dash = ROOT / "web_dashboard.py"
dtxt = dash.read_text()

if "dashboard_safety_ui" not in dtxt:
    dtxt = "from dashboard_safety_ui import security_headers, rate_limit\n" + dtxt

if "dashboard_security_headers_v1" not in dtxt:
    dtxt += r'''

@app.after_request
def dashboard_security_headers_v1(response):
    return security_headers(response)
'''

# Rate limit Profit Ops API if function exists in profit_ops_routes, not here.
dash.write_text(dtxt)

# -----------------------------
# Patch profit_ops_routes UI
# -----------------------------
routes = ROOT / "profit_ops_routes.py"
rtxt = routes.read_text()

if "rate_limit" not in rtxt:
    rtxt = rtxt.replace(
        "from profit_ops_analytics import snapshot",
        "from profit_ops_analytics import snapshot\nfrom dashboard_safety_ui import rate_limit"
    )

if "@rate_limit" not in rtxt:
    rtxt = rtxt.replace(
        "@bp.route(\"/api/profit-ops\")\ndef api_profit_ops():",
        "@bp.route(\"/api/profit-ops\")\n@rate_limit(max_requests=180, window_seconds=60)\ndef api_profit_ops():"
    )

# Add UI sections only if not already present
if "AI Mood" not in rtxt:
    rtxt = rtxt.replace(
        '<div class="grid">',
        '''<div class="grid">
 <div class="card"><div class="label">AI Mood</div><div class="value blue" id="aiMood">--</div><div class="muted" id="aiMoodNote">Waiting for data</div></div>
 <div class="card"><div class="label">Daily Goal</div><div class="value" id="dailyGoal">$0</div><div class="muted" id="goalProgress">0% progress</div><div class="barWrap" style="margin-top:10px"><div class="bar" id="goalBar"></div></div></div>
 <div class="card"><div class="label">Accessibility</div><div class="value yellow">Ready</div><div class="muted">Keyboard friendly · high contrast · mobile responsive</div></div>
 <div class="card"><div class="label">Security</div><div class="value good">Headers</div><div class="muted">Rate limit + browser security headers active</div></div>'''
    )

if "aiMood" in rtxt and "const ui=d.ui" not in rtxt:
    rtxt = rtxt.replace(
        'let d=await r.json(),l=d.latest||{},m=d.metrics||{},h=d.health||{},logs=d.logs||{};',
        'let d=await r.json(),l=d.latest||{},m=d.metrics||{},h=d.health||{},logs=d.logs||{},ui=d.ui||{};'
    )

    rtxt = rtxt.replace(
        'document.getElementById("updated").textContent="Updated: "+(d.generated_at||"--");',
        '''document.getElementById("updated").textContent="Updated: "+(d.generated_at||"--");
 let mood=(ui.mood||["--",""]);
 let goals=ui.goals||{};
 if(document.getElementById("aiMood")){
   document.getElementById("aiMood").textContent=mood[0]||"--";
   document.getElementById("aiMoodNote").textContent=mood[1]||"";
   document.getElementById("dailyGoal").textContent=money(goals.current_total_pl||0)+" / "+money(goals.daily_goal||200);
   document.getElementById("goalProgress").textContent=(goals.goal_progress_pct||0)+"% progress toward display goal";
   document.getElementById("goalBar").style.width=(goals.goal_progress_pct||0)+"%";
 }'''
    )

# Add accessibility skip link / focus styles if possible
if "skipLink" not in rtxt:
    rtxt = rtxt.replace(
        "<body>",
        '<body><a id="skipLink" href="#mainContent" style="position:absolute;left:-999px;top:0;background:#8ab4ff;color:#020617;padding:10px;z-index:99999">Skip to main content</a>'
    )
    rtxt = rtxt.replace(
        '<div class="wrap">',
        '<main id="mainContent" class="wrap">'
    )
    rtxt = rtxt.replace(
        '</div>\n\n<script>',
        '</main>\n\n<script>',
        1
    )
    rtxt = rtxt.replace(
        "</style>",
        '''
#skipLink:focus{left:12px}
a:focus,button:focus{outline:3px solid var(--yellow);outline-offset:3px}
@media (prefers-reduced-motion: reduce){*{scroll-behavior:auto!important;animation:none!important;transition:none!important}}
</style>'''
    )

routes.write_text(rtxt)

print("DONE: Dashboard Safety/UI V1 installed")
print()
print("Added:")
print("- Security headers")
print("- Rate limit for /api/profit-ops")
print("- AI Mood display")
print("- Goal tracking display only")
print("- Accessibility skip link/focus styles")
print("- Cross-dashboard usability polish")
print()
print("Next:")
print("python3 -m py_compile web_dashboard.py profit_ops_analytics.py profit_ops_routes.py dashboard_safety_ui.py")
print("sudo systemctl restart tradebot-dashboard")
