from pathlib import Path
import json

ROOT = Path(".")
APP = ROOT / "new_ponder_site"
T = APP / "templates"
S = APP / "static"
T.mkdir(parents=True, exist_ok=True)
S.mkdir(parents=True, exist_ok=True)

(APP / "site_config.json").write_text(json.dumps({
    "site_name": "Ponder Invest AI",
    "accent": "blue",
    "refresh_seconds": 30,
    "research_only": True
}, indent=2))

(APP / "app.py").write_text(r'''
from flask import Flask, render_template
import json
from pathlib import Path

app = Flask(__name__)
ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "static" / "research"

def load_json(name):
    p = RESEARCH / name
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}

@app.route("/")
def dashboard():
    ai = load_json("ai_summary_latest.json")
    alerts = load_json("notifications_latest.json")
    return render_template("dashboard.html", ai=ai, alerts=alerts)

@app.route("/research")
def research():
    data = {
        "ai": load_json("ai_summary_latest.json"),
        "alerts": load_json("notifications_latest.json"),
        "market": load_json("market_intelligence_latest.json"),
        "overnight": load_json("overnight_brief_latest.json"),
        "sell": load_json("sell_intelligence_latest.json"),
        "rotation": load_json("rotation_engine_latest.json"),
        "performance": load_json("rotation_performance_latest.json"),
        "shadow": load_json("shadow_capital_allocator_latest.json"),
        "regime": load_json("market_regime_filter_latest.json"),
    }
    return render_template("research.html", data=data)

@app.route("/assistant")
def assistant():
    ai = load_json("ai_summary_latest.json")
    assistant = load_json("ponder_assistant_latest.json")
    return render_template("assistant.html", ai=ai, assistant=assistant)

@app.route("/learning")
def learning():
    achievements = load_json("achievements_latest.json")
    performance = load_json("rotation_performance_latest.json")
    return render_template("learning.html", achievements=achievements, performance=performance)

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/health")
def health():
    return {"status": "ok", "site": "new_ponder_site"}

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050)
''')

(T / "base.html").write_text(r'''
<!doctype html>
<html>
<head>
  <title>Ponder Invest AI</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <aside class="side">
    <div class="brand">🐾 Ponder<span>AI</span></div>
    <p class="sub">Research-only command center</p>
    <a href="/">Dashboard</a>
    <a href="/research">Research</a>
    <a href="/assistant">Ask Ponder</a>
    <a href="/learning">Learning</a>
    <a href="/settings">Settings</a>
  </aside>

  <main class="main">
    {% block content %}{% endblock %}
  </main>
</body>
</html>
''')

(T / "dashboard.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
<h1>Ponder Invest AI</h1>
<p class="muted">Clean dashboard shell. Research-only. No live orders.</p>

{% set read = ai.get("key_readout", {}) %}
<section class="grid">
  <div class="card"><h3>Regime</h3><div class="big">{{ read.get("regime", "—") }}</div></div>
  <div class="card"><h3>News Impact</h3><div class="big">{{ read.get("news_impact", "—") }}</div></div>
  <div class="card"><h3>Top Rotation</h3><div class="big">{{ read.get("top_rotation", {}).get("move", "—") }}</div><p>{{ read.get("top_rotation", {}).get("action", "") }}</p></div>
  <div class="card"><h3>Alerts</h3><div class="big">{{ alerts.get("summary", {}).get("total", 0) }}</div></div>
</section>

<section class="card">
  <h2>What Should I Do?</h2>
  <ul>
    {% for item in ai.get("action_items", []) %}
      <li>{{ item }}</li>
    {% else %}
      <li>No action items yet.</li>
    {% endfor %}
  </ul>
</section>

<section class="card">
  <h2>Plain-English Summary</h2>
  <ul>
    {% for item in ai.get("plain_english_summary", []) %}
      <li>{{ item }}</li>
    {% else %}
      <li>No summary yet.</li>
    {% endfor %}
  </ul>
</section>
{% endblock %}
''')

(T / "research.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
<h1>Research Center</h1>
<p class="muted">All current non-live research modules in one clean place.</p>

<div class="tabs">
  <button onclick="showTab('ai')">AI Summary</button>
  <button onclick="showTab('alerts')">Alerts</button>
  <button onclick="showTab('market')">Market</button>
  <button onclick="showTab('overnight')">Overnight</button>
  <button onclick="showTab('sell')">Sell</button>
  <button onclick="showTab('rotation')">Rotation</button>
  <button onclick="showTab('performance')">Performance</button>
</div>

{% for name, value in data.items() %}
<section id="tab-{{ name }}" class="tab card" style="display:none">
  <h2>{{ name|title }}</h2>
  <pre>{{ value | tojson(indent=2) }}</pre>
</section>
{% endfor %}

<script>
function showTab(name){
  document.querySelectorAll('.tab').forEach(x => x.style.display='none');
  document.getElementById('tab-'+name).style.display='block';
}
showTab('ai');
</script>
{% endblock %}
''')

(T / "assistant.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
<h1>🐕 Ask Ponder</h1>
<p class="muted">Your dog-themed AI assistant layer, powered by current research JSON.</p>

<section class="card">
  <button onclick="answer('why_no_trade')">Why didn’t you trade?</button>
  <button onclick="answer('what_to_do')">What should I do now?</button>
  <button onclick="answer('biggest_risk')">Biggest risk?</button>
  <button onclick="answer('plain_english')">Explain simply</button>
</section>

<section class="card" id="answer">Click a question.</section>

<script>
const answers = {{ assistant.get("answers", {}) | tojson }};
const fallback = {{ ai.get("action_items", []) | tojson }};
function answer(key){
  const items = answers[key] || fallback || ["No answer yet."];
  document.getElementById("answer").innerHTML = "<ul>" + items.map(x => `<li>${x}</li>`).join("") + "</ul>";
}
</script>
{% endblock %}
''')

(T / "learning.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
<h1>Learning Center</h1>
<section class="grid">
  <div class="card"><h3>Achievements</h3><div class="big">{{ achievements.get("total_unlocked", achievements.get("achievements", [])|length) }}</div></div>
  <div class="card"><h3>Pending Evaluations</h3><div class="big">{{ performance.get("summary", {}).get("pending_evaluations", 0) }}</div></div>
</section>

<section class="card">
  <h2>Daily Missions</h2>
  <ul>
    <li>Review AI Summary.</li>
    <li>Check Alerts before strategy changes.</li>
    <li>Let tracker collect more outcomes.</li>
    <li>Do not connect experimental modules to live trading yet.</li>
  </ul>
</section>
{% endblock %}
''')

(T / "settings.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
<h1>Settings</h1>
<section class="card">
  <p>Next step: make theme, layout, refresh rate, and enabled modules editable from <code>site_config.json</code>.</p>
</section>
{% endblock %}
''')

(S / "style.css").write_text(r'''
:root{
  --bg:#020617;
  --panel:#07111f;
  --card:#0b1220;
  --border:#263349;
  --text:#f8fafc;
  --muted:#a8b3c7;
  --accent:#93c5fd;
  --good:#86efac;
  --warn:#facc15;
  --risk:#fb7185;
}
*{box-sizing:border-box}
body{
  margin:0;
  background:var(--bg);
  color:var(--text);
  font-family:system-ui,-apple-system,Segoe UI,sans-serif;
}
.side{
  position:fixed;
  top:0;left:0;bottom:0;
  width:250px;
  background:#050b16;
  border-right:1px solid var(--border);
  padding:22px;
}
.brand{font-size:26px;font-weight:950}
.brand span{color:var(--accent)}
.sub{color:var(--muted);font-size:13px;margin-bottom:24px}
.side a{
  display:block;
  color:#dbeafe;
  text-decoration:none;
  padding:13px 14px;
  margin:7px 0;
  border-radius:14px;
  border:1px solid transparent;
  font-weight:800;
}
.side a:hover{border-color:var(--accent);background:rgba(147,197,253,.08)}
.main{
  margin-left:250px;
  padding:34px;
  max-width:1500px;
}
h1{font-size:42px;margin:0 0 8px}
h2{margin-top:0}
.muted{color:var(--muted)}
.grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
  gap:16px;
  margin:22px 0;
}
.card{
  background:linear-gradient(180deg,var(--card),var(--panel));
  border:1px solid var(--border);
  border-radius:20px;
  padding:20px;
  margin:16px 0;
}
.big{font-size:30px;font-weight:950}
button{
  border:1px solid var(--border);
  background:#0b1220;
  color:white;
  border-radius:14px;
  padding:11px 14px;
  font-weight:850;
  cursor:pointer;
  margin:4px;
}
button:hover{border-color:var(--accent)}
pre{
  white-space:pre-wrap;
  overflow:auto;
  background:#020617;
  border:1px solid var(--border);
  border-radius:14px;
  padding:14px;
  max-height:650px;
}
.tabs{margin:18px 0}
@media(max-width:850px){
  .side{position:static;width:auto}
  .main{margin-left:0;padding:20px}
}
''')

print("✅ New independent Ponder site created in new_ponder_site/")
print("Run it with: cd /home/ubuntu/trading-bot && python3 new_ponder_site/app.py")
print("Open locally: http://127.0.0.1:5050")
