from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_app_ui_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

# --------------------------------------------------
# 1. Add rotation readiness + decay-style pressure
# --------------------------------------------------
if '"readiness":' not in txt:
    txt = txt.replace(
        '"simulated_improvement": simulated_improvement,',
        '''"simulated_improvement": simulated_improvement,
            "readiness": "NOT READY",
            "held_losing_for": "collecting",
            "readiness_reason": "Need 15–20 closed trades before automation.",'''
    )

    txt = txt.replace(
        '"simulated_improvement": 0,',
        '''"simulated_improvement": 0,
            "readiness": "NOT READY",
            "held_losing_for": "collecting",
            "readiness_reason": "Suggestion-only mode.",'''
    )

# Add table headers
txt = txt.replace(
    '<th>If Rotated</th><th>Reason</th>',
    '<th>If Rotated</th><th>Readiness</th><th>Decay Timer</th><th>Reason</th>'
)

# Add JS row fields
txt = txt.replace(
    '<td>${money(x.simulated_improvement||0)}</td>\n        <td>${x.reason||\'\'}</td>',
    '''<td>${money(x.simulated_improvement||0)}</td>
        <td class="${(x.readiness||'').includes('READY') && !(x.readiness||'').includes('NOT') ? 'good':'warn'}">${x.readiness||'NOT READY'}</td>
        <td>${x.held_losing_for||'collecting'}</td>
        <td>${x.reason||''}<br><span class="muted">${x.readiness_reason||''}</span></td>'''
)

# --------------------------------------------------
# 2. Add polished app-style nav/sidebar/header
# --------------------------------------------------
if "APP_UI_V1" not in txt:
    txt = txt.replace(
        '<body>',
        '''<body>
<!-- APP_UI_V1 -->
<a class="skip" href="#main">Skip to dashboard</a>
<div class="appShell">
  <aside class="sidebar">
    <div class="brand">🐾 Ponder<span>AI</span></div>
    <a href="/" class="navItem">🏠 Main</a>
    <a href="/profit" class="navItem">📈 Profit Ops</a>
    <a href="/profit-lab" class="navItem active">🧠 Profit Lab</a>
    <a href="/history" class="navItem">📜 History</a>
    <a href="/logout" class="navItem">🔐 Logout</a>
    <div class="sideNote">Suggestion-only mode<br>No trades executed here.</div>
  </aside>
  <main id="main" class="appMain">'''
    )

    txt = txt.replace(
        '</body>',
        '''</main>
</div>
</body>'''
    )

# Hide old top nav links but keep content
txt = txt.replace(
    '<div><a href="/">Main</a> · <a href="/profit">Profit Ops</a> · <a href="/profit-lab">Profit Lab</a></div>',
    '<div class="topStatus">Live · Read-only · Dashboard Safe</div>'
)

# --------------------------------------------------
# 3. Upgrade CSS for app look/readability/accessibility
# --------------------------------------------------
if ".appShell" not in txt:
    txt = txt.replace(
        '</style>',
        '''
.sidebar{
  position:fixed;left:0;top:0;bottom:0;width:230px;
  background:rgba(5,10,24,.92);border-right:1px solid var(--border);
  padding:22px 16px;z-index:10;backdrop-filter:blur(12px)
}
.brand{font-size:24px;font-weight:900;margin-bottom:24px}
.brand span{color:var(--green)}
.navItem{
  display:block;padding:12px 14px;border-radius:14px;color:#dbe7ff;
  margin:8px 0;background:rgba(255,255,255,.03)
}
.navItem:hover,.navItem.active{background:rgba(138,180,255,.14);color:white}
.sideNote{position:absolute;bottom:20px;color:var(--muted);font-size:12px;line-height:1.4}
.appMain{margin-left:230px;min-height:100vh}
.wrap{max-width:1320px}
.card{transition:.18s ease;overflow:hidden}
.card:hover{transform:translateY(-1px);border-color:rgba(138,180,255,.45)}
.value{letter-spacing:.2px}
.topStatus{
  color:var(--green);font-weight:800;background:rgba(124,255,155,.1);
  border:1px solid rgba(124,255,155,.2);padding:8px 12px;border-radius:999px
}
.skip{position:absolute;left:-999px;top:8px;background:var(--blue);color:#06101f;padding:10px;z-index:999}
.skip:focus{left:8px}
button{
  padding:9px 12px;border-radius:12px;border:1px solid var(--border);
  background:#0b1225;color:white;cursor:pointer
}
button:hover{border-color:var(--blue)}
input{font-size:14px}
@media(max-width:950px){
  .sidebar{position:static;width:auto;border-right:0;border-bottom:1px solid var(--border)}
  .sideNote{position:static;margin-top:12px}
  .appMain{margin-left:0}
  .navItem{display:inline-block;margin:4px}
}
@media (prefers-reduced-motion: reduce){
  *{animation:none!important;transition:none!important;scroll-behavior:auto!important}
}
</style>'''
    )

# --------------------------------------------------
# 4. Add UI summary chips above chart
# --------------------------------------------------
if "Quick Status" not in txt:
    txt = txt.replace(
        '<div class="card">\n    <h2>Equity Lab Chart</h2>',
        '''<div class="card">
    <h2>⚡ Quick Status</h2>
    <div class="grid">
      <div><div class="label">Mode</div><div class="value info">Read Only</div></div>
      <div><div class="label">Rotation</div><div class="value warn">Suggest</div></div>
      <div><div class="label">Automation Readiness</div><div class="value warn">Not Ready</div></div>
      <div><div class="label">Next Milestone</div><div class="value">15–20 Trades</div></div>
    </div>
  </div>

  <div class="card">
    <h2>Equity Lab Chart</h2>'''
    )

# --------------------------------------------------
# 5. Improve Ponder rotation answer with readiness
# --------------------------------------------------
txt = txt.replace(
    'Important:\\nThis is suggestion-only. Do not enable auto-rotation until you have at least 15–20 closed trades and enough data to validate exits.`;',
    '''Readiness:
${main.readiness || "NOT READY"} — ${main.readiness_reason || "Need more closed trades."}

Decay timer:
${main.held_losing_for || "collecting"}

Important:
This is suggestion-only. Do not enable auto-rotation until you have at least 15–20 closed trades and enough data to validate exits.`;'''
)

p.write_text(txt)

print("DONE: Profit Lab App UI + Rotation Readiness installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
