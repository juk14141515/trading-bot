from pathlib import Path

ROOT = Path("/home/ubuntu/trading-bot/new_ponder_site")
T = ROOT / "templates"
S = ROOT / "static"

# ---------- APP ROUTES ----------
(ROOT / "app.py").write_text(r'''
from flask import Flask, render_template
import json
from pathlib import Path

app = Flask(__name__)
ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "static" / "research"

FEEDS = {
    "ai": "ai_summary_latest.json",
    "alerts": "notifications_latest.json",
    "market": "market_intelligence_latest.json",
    "overnight": "overnight_brief_latest.json",
    "sell": "sell_intelligence_latest.json",
    "rotation": "rotation_engine_latest.json",
    "performance": "rotation_performance_latest.json",
    "shadow": "shadow_capital_allocator_latest.json",
    "regime": "market_regime_filter_latest.json",
    "achievements": "achievements_latest.json",
    "assistant": "ponder_assistant_latest.json",
}

def load_json(name):
    p = RESEARCH / name
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception as e:
        return {"error": str(e), "file": name}

def data():
    return {k: load_json(v) for k, v in FEEDS.items()}

@app.route("/")
def dashboard():
    return render_template("dashboard.html", d=data())

@app.route("/research")
def research():
    return render_template("research.html", d=data())

@app.route("/assistant")
def assistant():
    return render_template("assistant.html", d=data())

@app.route("/capital")
def capital():
    return render_template("capital.html", d=data())

@app.route("/rotation")
def rotation():
    return render_template("rotation.html", d=data())

@app.route("/learning")
def learning():
    return render_template("learning.html", d=data())

@app.route("/settings")
def settings():
    return render_template("settings.html", d=data())

@app.route("/health")
def health():
    return {"status": "ok", "site": "new_ponder_site"}

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050)
''')

# ---------- BASE ----------
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
    <p class="sub">Research-only autonomous trading command center.</p>
    <a href="/">🏠 Command</a>
    <a href="/research">🧠 Research</a>
    <a href="/assistant">🐕 Ask Ponder</a>
    <a href="/capital">💰 Capital AI</a>
    <a href="/rotation">🔁 Rotation Lab</a>
    <a href="/learning">🎮 Learning</a>
    <a href="/settings">⚙️ Settings</a>
  </aside>

  <main class="main">
    {% block content %}{% endblock %}
  </main>
</body>
</html>
''')

# ---------- DASHBOARD ----------
(T / "dashboard.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
{% set ai = d.ai %}
{% set read = ai.get("key_readout", {}) %}
{% set alerts = d.alerts.get("summary", {}) %}
{% set perf = d.performance.get("summary", {}) %}

<section class="hero">
  <div>
    <div class="eyebrow">RESEARCH MODE · NO LIVE ORDERS</div>
    <h1>Ponder Invest AI Command Center</h1>
    <p class="muted">Market intelligence, capital discipline, rotation learning, and future automation readiness.</p>
  </div>
  <div class="heroBox">
    <div class="dog">🐕</div>
    <div><b>Ponder is guarding the system.</b><p class="muted">Risk first. Quality over quantity.</p></div>
  </div>
</section>

<section class="grid kpi">
  <div class="card"><h3>Regime</h3><div class="big">{{ read.get("regime","—") }}</div><p>Score {{ read.get("regime_score","—") }}</p></div>
  <div class="card"><h3>News Impact</h3><div class="big">{{ read.get("news_impact","—") }}</div><p>High news = defensive</p></div>
  <div class="card"><h3>Top Rotation</h3><div class="big small">{{ read.get("top_rotation",{}).get("move","—") }}</div><p>{{ read.get("top_rotation",{}).get("action","") }}</p></div>
  <div class="card"><h3>Alerts</h3><div class="big">{{ alerts.get("total",0) }}</div><p>{{ alerts.get("critical",0) }} critical · {{ alerts.get("warning",0) }} warnings</p></div>
  <div class="card"><h3>Pending Learning</h3><div class="big">{{ perf.get("pending_evaluations", read.get("pending_evaluations","—")) }}</div><p>Signals awaiting outcome</p></div>
  <div class="card"><h3>Automation</h3><div class="big warnText">Locked</div><p>Waiting for proven edge</p></div>
</section>

<section class="split">
  <div class="card highlight">
    <h2>🧭 What Should I Do?</h2>
    <ul>{% for x in ai.get("action_items",[]) %}<li>{{ x }}</li>{% else %}<li>Review AI Summary, Alerts, and Rotation before making changes.</li>{% endfor %}</ul>
  </div>
  <div class="card">
    <h2>🧠 System Readiness</h2>
    <div class="check">🟢 Research data active</div>
    <div class="check">🟡 More rotation outcomes needed</div>
    <div class="check">🟡 Adaptive allocator next</div>
    <div class="check">🔴 Live automation disabled</div>
  </div>
</section>

<section class="grid">
  <a class="card link" href="/capital"><h3>💰 Adaptive Capital AI</h3><p>Unused capital, position sizing, risk mode, and allocation suggestions.</p></a>
  <a class="card link" href="/rotation"><h3>🔁 Rotation Lab</h3><p>Sell weakest → buy strongest research with confidence and performance checks.</p></a>
  <a class="card link" href="/research"><h3>🧠 Full Research</h3><p>AI summary, market, overnight, sell, alerts, shadow, and performance feeds.</p></a>
  <a class="card link" href="/learning"><h3>🎮 Learning Layer</h3><p>Daily missions, XP, achievements, and automation readiness.</p></a>
</section>

<section class="card">
  <h2>Plain-English Summary</h2>
  <ul>{% for x in ai.get("plain_english_summary",[]) %}<li>{{ x }}</li>{% else %}<li>No summary yet.</li>{% endfor %}</ul>
</section>
{% endblock %}
''')

# ---------- CAPITAL ----------
(T / "capital.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
{% set shadow = d.shadow %}
{% set ai = d.ai %}
{% set read = ai.get("key_readout", {}) %}
<h1>💰 Adaptive Capital AI</h1>
<p class="muted">Research-only allocation command center. This does not place trades.</p>

<section class="grid">
  <div class="card"><h3>Risk Mode</h3><div class="big">{{ read.get("regime","—") }}</div><p>Allocator should respect market regime.</p></div>
  <div class="card"><h3>News Impact</h3><div class="big">{{ read.get("news_impact","—") }}</div><p>High news reduces aggression.</p></div>
  <div class="card"><h3>Capital Engine</h3><div class="big warnText">Next</div><p>adaptive_allocator_v1.py</p></div>
  <div class="card"><h3>Cash Optimizer</h3><div class="big warnText">Next</div><p>cash_optimizer_v1.py</p></div>
</section>

<section class="card highlight">
  <h2>Allocator Rules to Build</h2>
  <ul>
    <li>If rotation confidence is HIGH and capital utilization is below 70%, recommend larger allocation.</li>
    <li>If recent rotations are losing, reduce allocation and tighten filters.</li>
    <li>Never increase size during Risk-Off or high news impact unless edge is proven.</li>
    <li>Output: recommended_position_size_pct, risk_mode, reason, and confidence.</li>
  </ul>
</section>

<section class="card">
  <h2>Current Shadow / Capital Feed</h2>
  <pre>{{ shadow | tojson(indent=2) }}</pre>
</section>
{% endblock %}
''')

# ---------- ROTATION ----------
(T / "rotation.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
{% set rot = d.rotation %}
{% set perf = d.performance %}
<h1>🔁 Rotation Lab</h1>
<p class="muted">Research-only sell weakest → buy strongest intelligence.</p>

<section class="grid">
  <div class="card"><h3>Rotation Engine</h3><div class="big">v2</div><p>Research-only</p></div>
  <div class="card"><h3>Performance Tracker</h3><div class="big">{{ perf.get("summary",{}).get("evaluated",0) }}</div><p>Evaluated outcomes</p></div>
  <div class="card"><h3>Pending</h3><div class="big">{{ perf.get("summary",{}).get("pending_evaluations",0) }}</div><p>Waiting for outcome</p></div>
  <div class="card"><h3>Live Mode</h3><div class="big riskText">Off</div><p>Correct for now</p></div>
</section>

<section class="card highlight">
  <h2>Decision Mode Criteria</h2>
  <ul>
    <li>sell_pressure &gt; 60</li>
    <li>rotation_score &gt; 65</li>
    <li>expected_edge &gt; 10</li>
    <li>entry_zone is Healthy or Pullback</li>
    <li>avoid weak swaps where buy_score &lt; sell_pressure</li>
  </ul>
</section>

<section class="card">
  <h2>Rotation Feed</h2>
  <pre>{{ rot | tojson(indent=2) }}</pre>
</section>

<section class="card">
  <h2>Performance Feed</h2>
  <pre>{{ perf | tojson(indent=2) }}</pre>
</section>
{% endblock %}
''')

# ---------- RESEARCH ----------
(T / "research.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
<h1>🧠 Research Center</h1>
<p class="muted">Full intelligence map. Organized but still detailed.</p>

<div class="tabs">
{% for name in ["ai","alerts","market","overnight","sell","rotation","performance","shadow","regime"] %}
  <button onclick="showTab('{{ name }}')">{{ name|title }}</button>
{% endfor %}
</div>

{% for name, value in d.items() %}
<section id="tab-{{ name }}" class="tab card" style="display:none">
  <h2>{{ name|title }}</h2>
  {% if name == "ai" %}
    <h3>Action Items</h3><ul>{% for x in value.get("action_items",[]) %}<li>{{ x }}</li>{% endfor %}</ul>
    <h3>Plain English</h3><ul>{% for x in value.get("plain_english_summary",[]) %}<li>{{ x }}</li>{% endfor %}</ul>
  {% elif name == "alerts" %}
    <table><tr><th>Level</th><th>Category</th><th>Title</th><th>Message</th></tr>
    {% for a in value.get("alerts",[]) %}<tr><td>{{ a.level }}</td><td>{{ a.category }}</td><td>{{ a.title }}</td><td>{{ a.message }}</td></tr>{% endfor %}
    </table>
  {% endif %}
  <h3>Raw Feed</h3>
  <pre>{{ value | tojson(indent=2) }}</pre>
</section>
{% endfor %}

<script>
function showTab(name){
  document.querySelectorAll('.tab').forEach(x=>x.style.display='none');
  document.getElementById('tab-'+name).style.display='block';
}
showTab('ai');
</script>
{% endblock %}
''')

# ---------- SETTINGS ----------
(T / "settings.html").write_text(r'''
{% extends "base.html" %}
{% block content %}
<h1>⚙️ Settings & Editor Plan</h1>
<p class="muted">This page will become the easy website editor.</p>

<section class="grid">
  <div class="card"><h3>Theme</h3><button>Blue</button><button>Slate</button><button>Purple</button></div>
  <div class="card"><h3>Modes</h3><button>Simple</button><button>Full</button><button>Colorblind</button></div>
  <div class="card"><h3>Refresh</h3><button>Manual</button><button>30s</button><button>60s</button></div>
</section>

<section class="card highlight">
  <h2>Easy Edit System Coming</h2>
  <ul>
    <li><code>site_config.json</code> controls pages, theme, refresh, and modules.</li>
    <li><code>modules/</code> controls feature cards.</li>
    <li>No more giant injections.</li>
    <li>Future modules become plug-in style.</li>
  </ul>
</section>
{% endblock %}
''')

# ---------- CSS ----------
(S / "style.css").write_text(r'''
:root{
  --bg:#020617;--panel:#07111f;--card:#0b1220;--border:#334155;
  --text:#f8fafc;--muted:#a8b3c7;--accent:#93c5fd;--good:#86efac;--warn:#facc15;--risk:#fb7185;
}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at top right,#111b3a,#020617 45%);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,sans-serif}
.side{position:fixed;inset:0 auto 0 0;width:250px;background:rgba(5,11,22,.96);border-right:1px solid var(--border);padding:22px}
.brand{font-size:26px;font-weight:950}.brand span{color:var(--accent)}.sub{color:var(--muted);font-size:13px;margin-bottom:22px}
.side a{display:block;color:#dbeafe;text-decoration:none;padding:13px 14px;margin:7px 0;border-radius:14px;border:1px solid transparent;font-weight:850}
.side a:hover{border-color:var(--accent);background:rgba(147,197,253,.08)}
.main{margin-left:250px;padding:34px;max-width:1600px}
h1{font-size:42px;margin:0 0 8px}h2{margin-top:0}.muted{color:var(--muted)}
.hero{display:flex;justify-content:space-between;gap:20px;align-items:center;border:1px solid var(--border);border-radius:24px;padding:26px;background:linear-gradient(135deg,rgba(147,197,253,.12),rgba(7,17,31,.95));margin-bottom:22px}
.eyebrow{color:var(--accent);font-weight:950;font-size:12px;letter-spacing:.08em}
.heroBox{display:flex;gap:14px;align-items:center;min-width:280px}.dog{width:74px;height:74px;border:1px solid var(--accent);border-radius:24px;display:flex;align-items:center;justify-content:center;font-size:34px;background:rgba(147,197,253,.08)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px;margin:20px 0}
.card{background:linear-gradient(180deg,rgba(15,23,42,.96),rgba(7,17,31,.96));border:1px solid var(--border);border-radius:20px;padding:20px;margin:16px 0;box-shadow:0 20px 60px rgba(0,0,0,.18)}
.card h3{color:#bfdbfe;margin-top:0}.big{font-size:30px;font-weight:950}.small{font-size:23px}
.highlight{border-color:rgba(147,197,253,.65);box-shadow:0 0 0 1px rgba(147,197,253,.1)}
.split{display:grid;grid-template-columns:1.4fr .8fr;gap:16px}.check{margin:11px 0;color:var(--muted)}
.link{text-decoration:none;color:var(--text)}.link:hover{border-color:var(--accent);transform:translateY(-2px)}
.warnText{color:var(--warn)}.riskText{color:var(--risk)}
button{background:#0b1220;color:white;border:1px solid var(--border);border-radius:14px;padding:11px 14px;font-weight:850;cursor:pointer;margin:4px}
button:hover{border-color:var(--accent)}.tabs{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0}
pre{white-space:pre-wrap;overflow:auto;max-height:620px;background:#020617;border:1px solid var(--border);border-radius:14px;padding:14px}
table{width:100%;border-collapse:collapse}th,td{padding:10px;border-bottom:1px solid rgba(148,163,184,.22);text-align:left}
li{margin:7px 0;line-height:1.45}
@media(max-width:950px){.side{position:static;width:auto}.main{margin-left:0;padding:20px}.split,.hero{grid-template-columns:1fr;display:block}}
''')

print("✅ Max v3 installed")
