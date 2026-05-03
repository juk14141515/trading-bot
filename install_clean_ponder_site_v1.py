from pathlib import Path
import re

ROOT = Path(".")
T = ROOT / "templates"
S = ROOT / "static" / "site"
T.mkdir(exist_ok=True)
(S / "css").mkdir(parents=True, exist_ok=True)
(S / "js").mkdir(parents=True, exist_ok=True)

Path("web_dashboard.py.bak_clean_site_v1").write_text(Path("web_dashboard.py").read_text())

(T / "base.html").write_text("""<!doctype html>
<html>
<head>
  <title>Ponder Invest AI</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="/static/site/css/app.css?v=clean1">
</head>
<body>
  <aside class="sidebar">
    <div class="brand">🐾 Ponder<span>AI</span></div>
    <a href="/">Dashboard</a>
    <a href="/profit">Profit Ops</a>
    <a href="/profit-lab">Profit Lab</a>
    <a href="/research">Research</a>
    <a href="/learning">Learning</a>
    <a href="/settings">Settings</a>
    <a href="/history">History</a>
    <a href="/logout">Logout</a>
  </aside>

  <main class="main">
    {% block content %}{% endblock %}
  </main>

  <button id="ponderAssistantBtn">🐕</button>
  <section id="ponderPanel"></section>

  <script src="/static/site/js/app.js?v=clean1"></script>
</body>
</html>
""")

(T / "dashboard.html").write_text("""{% extends "base.html" %}
{% block content %}
<h1>Dashboard</h1>
<p class="muted">Clean command center for Ponder Invest AI.</p>
<div id="overviewCards" class="grid"></div>
<div class="card">
  <h2>What Should I Do?</h2>
  <ul id="actionItems"></ul>
</div>
{% endblock %}
""")

(T / "research.html").write_text("""{% extends "base.html" %}
{% block content %}
<h1>Research Center</h1>
<div class="tabs">
  <button data-tab="ai">AI Summary</button>
  <button data-tab="alerts">Alerts</button>
  <button data-tab="market">Market</button>
  <button data-tab="overnight">Overnight</button>
  <button data-tab="sell">Sell</button>
  <button data-tab="rotation">Rotation</button>
  <button data-tab="performance">Performance</button>
  <button data-tab="debug">Debug</button>
</div>
<div id="researchContent" class="card"></div>
<script src="/static/site/js/research.js?v=clean1"></script>
{% endblock %}
""")

(T / "learning.html").write_text("""{% extends "base.html" %}
{% block content %}
<h1>Learning Center</h1>
<div id="learningContent" class="grid"></div>
{% endblock %}
""")

(T / "settings.html").write_text("""{% extends "base.html" %}
{% block content %}
<h1>Settings</h1>
<div class="card">
  <button onclick="localStorage.clear(); location.reload()">Reset Local UI Settings</button>
  <button onclick="copyDebug()">Copy Debug Snapshot</button>
</div>
{% endblock %}
""")

(S / "css" / "app.css").write_text("""
:root{
  --bg:#020617; --panel:#07111f; --card:#0b1220; --border:#263349;
  --text:#f8fafc; --muted:#a8b3c7; --accent:#93c5fd;
  --good:#86efac; --warn:#facc15; --risk:#fb7185;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,sans-serif}
.sidebar{position:fixed;left:0;top:0;bottom:0;width:240px;background:#050b16;border-right:1px solid var(--border);padding:20px;display:flex;flex-direction:column;gap:8px}
.brand{font-size:24px;font-weight:950;margin-bottom:16px}.brand span{color:var(--accent)}
.sidebar a{color:#dbeafe;text-decoration:none;padding:12px 14px;border-radius:14px;border:1px solid transparent;font-weight:800}
.sidebar a:hover{border-color:var(--accent);background:rgba(147,197,253,.08)}
.main{margin-left:240px;padding:28px;max-width:1500px}
h1{font-size:38px;margin:0 0 8px}.muted{color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:18px 0}
.card{background:linear-gradient(180deg,#0b1220,#07111f);border:1px solid var(--border);border-radius:20px;padding:18px;margin:14px 0}
.big{font-size:28px;font-weight:950}.badge{display:inline-block;border:1px solid var(--border);border-radius:999px;padding:4px 9px;font-weight:850}
.tabs{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}.tabs button,button{border:1px solid var(--border);background:#0b1220;color:white;border-radius:14px;padding:10px 13px;font-weight:850;cursor:pointer}
button:hover{border-color:var(--accent)}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:10px;border-bottom:1px solid rgba(148,163,184,.22);text-align:left;vertical-align:top}th{color:var(--accent)}
#ponderAssistantBtn{position:fixed;right:24px;bottom:92px;width:62px;height:62px;border-radius:22px;background:#07111f;border:2px solid var(--accent);color:white;font-size:28px;cursor:pointer;box-shadow:0 18px 55px rgba(0,0,0,.55)}
#ponderPanel{display:none;position:fixed;right:24px;bottom:170px;width:420px;max-width:calc(100vw - 36px);background:#07111f;border:1px solid var(--border);border-radius:22px;box-shadow:0 30px 90px rgba(0,0,0,.7);padding:18px}
@media(max-width:850px){.sidebar{position:static;width:auto}.main{margin-left:0;padding:18px}}
""")

(S / "js" / "app.js").write_text("""
async function getJson(path){const r=await fetch(path+'?ts='+Date.now(),{cache:'no-store'});return r.ok?await r.json():{}}
function esc(v){return String(v??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#039;'}[c]))}
function card(t,v,n=''){return `<div class="card"><h3>${t}</h3><div class="big">${v??'—'}</div><p class="muted">${n}</p></div>`}

async function loadOverview(){
  const ai=await getJson('/static/research/ai_summary_latest.json');
  const alerts=await getJson('/static/research/notifications_latest.json');
  const read=ai.key_readout||{};
  const el=document.getElementById('overviewCards');
  if(el) el.innerHTML=[
    card('Regime', read.regime, 'Market mode'),
    card('News Impact', read.news_impact, 'Higher means more caution'),
    card('Top Rotation', (read.top_rotation||{}).move, (read.top_rotation||{}).action||''),
    card('Alerts', (alerts.summary||{}).total||0, `${(alerts.summary||{}).critical||0} critical`)
  ].join('');
  const actions=document.getElementById('actionItems');
  if(actions) actions.innerHTML=(ai.action_items||[]).map(x=>`<li>${esc(x)}</li>`).join('');
}

async function openPonder(){
  const p=document.getElementById('ponderPanel');
  const ai=await getJson('/static/research/ai_summary_latest.json');
  const assistant=await getJson('/static/research/ponder_assistant_latest.json');
  p.style.display=p.style.display==='block'?'none':'block';
  p.innerHTML=`<h2>🐕 Ask Ponder</h2>
    <button data-q="why_no_trade">Why didn’t you trade?</button>
    <button data-q="what_to_do">What should I do?</button>
    <button data-q="biggest_risk">Biggest risk?</button>
    <div id="ponderAnswer" class="card">Click a question.</div>`;
  p.querySelectorAll('[data-q]').forEach(b=>b.onclick=()=>{
    const items=(assistant.answers||{})[b.dataset.q] || ai.action_items || ['No answer yet.'];
    document.getElementById('ponderAnswer').innerHTML='<ul>'+items.map(x=>`<li>${esc(x)}</li>`).join('')+'</ul>';
  });
}
document.getElementById('ponderAssistantBtn')?.addEventListener('click',openPonder);
loadOverview();
setInterval(loadOverview,45000);

function copyDebug(){
  Promise.all([
    getJson('/static/research/ai_summary_latest.json'),
    getJson('/static/research/notifications_latest.json'),
    getJson('/static/research/rotation_engine_latest.json')
  ]).then(([ai,alerts,rotation])=>{
    navigator.clipboard.writeText(JSON.stringify({time:new Date().toISOString(),url:location.href,ai:ai.key_readout,alerts:alerts.summary,rotation:rotation.top_rotation},null,2));
    alert('Debug snapshot copied');
  });
}
""")

(S / "js" / "research.js").write_text("""
async function getJson(path){const r=await fetch(path+'?ts='+Date.now(),{cache:'no-store'});return r.ok?await r.json():{}}
function esc(v){return String(v??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#039;'}[c]))}
function table(rows,keys){return `<table><thead><tr>${keys.map(k=>`<th>${k}</th>`).join('')}</tr></thead><tbody>${(rows||[]).map(r=>`<tr>${keys.map(k=>`<td>${Array.isArray(r[k])?r[k].map(esc).join('<br>'):esc(r[k])}</td>`).join('')}</tr>`).join('')||`<tr><td colspan="${keys.length}">No data</td></tr>`}</tbody></table>`}

async function render(tab='ai'){
 const c=document.getElementById('researchContent');
 if(tab==='ai'){let d=await getJson('/static/research/ai_summary_latest.json');c.innerHTML=`<h2>AI Summary</h2><h3>What Should I Do?</h3><ul>${(d.action_items||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ul><h3>Simple Summary</h3><ul>${(d.plain_english_summary||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`}
 if(tab==='alerts'){let d=await getJson('/static/research/notifications_latest.json');c.innerHTML=`<h2>Alerts</h2>${table(d.alerts||[],['level','category','title','message'])}`}
 if(tab==='market'){let d=await getJson('/static/research/market_intelligence_latest.json');c.innerHTML=`<h2>Market</h2>${table(d.trade_ready||d.top_candidates||[],['symbol','final_score','score','entry_zone','label'])}`}
 if(tab==='overnight'){let d=await getJson('/static/research/overnight_brief_latest.json');c.innerHTML=`<h2>Overnight</h2><p>Market: ${esc(d.market_label)} | Risk: ${esc(d.risk_score)} | News: ${esc(d.news_impact)}</p><ul>${(d.notes||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`}
 if(tab==='sell'){let d=await getJson('/static/research/sell_intelligence_latest.json');c.innerHTML=`<h2>Sell Intelligence</h2>${table(d.sell_candidates||[],['symbol','sell_pressure','verdict','reasons'])}`}
 if(tab==='rotation'){let d=await getJson('/static/research/rotation_engine_latest.json');c.innerHTML=`<h2>Rotation</h2>${table(d.rotation_suggestions||[],['sell_symbol','buy_symbol','action','rotation_score','confidence','regime'])}`}
 if(tab==='performance'){let d=await getJson('/static/research/rotation_performance_latest.json');c.innerHTML=`<h2>Performance</h2><pre>${esc(JSON.stringify(d.summary||d,null,2))}</pre>`}
 if(tab==='debug'){c.innerHTML=`<h2>Debug</h2><button onclick="copyDebug()">Copy Debug Snapshot</button>`}
}
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>render(b.dataset.tab));
render('ai');
""")

# Patch Flask to add clean pages/routes and inject no old overlays
p = Path("web_dashboard.py")
text = p.read_text()

# remove old injected UI systems
text = re.sub(r'\n# === PONDER_.*?# === END[_A-Z]*PONDER.*?===\n', '\n', text, flags=re.S)
text = re.sub(r'\n?\s*<script src="/static/ponder_ui\.js\?v=[^"]+"></script>', '', text)
text = re.sub(r'\n?\s*<script src="/static/ponder[34]/[^"]+"></script>', '', text)
text = re.sub(r'\n?\s*<link rel="stylesheet" href="/static/ponder[34]/[^"]+">', '', text)

if "render_template" not in text.split("\n", 20)[0]:
    text = text.replace("render_template_string", "render_template, render_template_string", 1)

routes = '''
# === CLEAN_PONDER_SITE_V1 ===
@app.route("/research")
@requires_auth
def clean_research():
    return render_template("research.html")

@app.route("/learning")
@requires_auth
def clean_learning():
    return render_template("learning.html")

@app.route("/settings")
@requires_auth
def clean_settings():
    return render_template("settings.html")
# === END_CLEAN_PONDER_SITE_V1 ===
'''
if "CLEAN_PONDER_SITE_V1" not in text:
    marker = '@app.route("/history")'
    text = text.replace(marker, routes + "\\n" + marker)

# Replace dashboard route return template at end manually later if needed.
# For now keep existing dashboard/profit pages, but global old overlays removed.
p.write_text(text)

Path("rollback_clean_ponder_site_v1.sh").write_text("""#!/bin/bash
cd /home/ubuntu/trading-bot || exit 1
cp web_dashboard.py.bak_clean_site_v1 web_dashboard.py
sudo systemctl restart tradebot-dashboard.service
echo "Rolled back clean site v1."
""")

print("✅ Clean Ponder site files installed")
print("✅ New pages: /research /learning /settings")
print("✅ Rollback: bash rollback_clean_ponder_site_v1.sh")
