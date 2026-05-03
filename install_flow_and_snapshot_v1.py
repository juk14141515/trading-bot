from pathlib import Path

ROOT = Path("/home/ubuntu/trading-bot")
APP = ROOT / "new_ponder_site/app.py"
DASH = ROOT / "new_ponder_site/templates/dashboard.html"
BASE = ROOT / "new_ponder_site/templates/base.html"

# backup
for p in [APP, DASH, BASE]:
    p.write_text(p.read_text())

app = APP.read_text()

if '@app.route("/debug-snapshot")' not in app:
    app = app.replace(
'''@app.route("/health")
def health():''',
'''@app.route("/debug-snapshot")
@auth_required
def debug_snapshot():
    data = dashboard_data()
    files = {}
    for rel in [
        "new_ponder_site/app.py",
        "new_ponder_site/templates/base.html",
        "new_ponder_site/templates/dashboard.html",
        "new_ponder_site/templates/research.html",
        "new_ponder_site/templates/assistant.html",
        "new_ponder_site/templates/learning.html",
        "new_ponder_site/templates/settings.html",
        "new_ponder_site/static/style.css",
    ]:
        p = ROOT / rel
        files[rel] = p.read_text()[:12000] if p.exists() else "MISSING"

    return render_template("debug_snapshot.html", data=data, files=files)


@app.route("/health")
def health():'''
    )

APP.write_text(app)

(BASE).write_text('''<!doctype html>
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
    <a href="/debug-snapshot">Send to ChatGPT</a>
  </aside>

  <main class="main">
    {% block content %}{% endblock %}
  </main>
</body>
</html>
''')

(ROOT / "new_ponder_site/templates/debug_snapshot.html").write_text('''{% extends "base.html" %}
{% block content %}
<h1>📋 Send to ChatGPT</h1>
<p class="muted">Copy this page when you want help upgrading/debugging. It includes current data + key site files.</p>

<section class="card highlight">
  <h2>How to use</h2>
  <p>Click inside the box, press CTRL+A, then CTRL+C, and paste it into ChatGPT.</p>
</section>

<section class="card">
<pre style="white-space:pre-wrap; font-size:13px;">
===== PONDER SNAPSHOT =====

===== DASHBOARD DATA =====
{{ data | tojson(indent=2) }}

{% for name, content in files.items() %}
===== FILE: {{ name }} =====
{{ content }}
{% endfor %}
</pre>
</section>
{% endblock %}
''')

DASH.write_text('''{% extends "base.html" %}
{% block content %}

{% set ai = data.get("ai", {}) %}
{% set alerts = data.get("alerts", {}) %}
{% set rotation = data.get("rotation", {}) %}
{% set performance = data.get("performance", {}) %}
{% set shadow = data.get("shadow", {}) %}
{% set sell = data.get("sell", {}) %}
{% set regime = data.get("regime", {}) %}
{% set achievements = data.get("achievements", {}) %}
{% set read = ai.get("key_readout", {}) %}
{% set alerts_sum = alerts.get("summary", {}) %}

{% set regime_text = read.get("regime", regime.get("regime", "Unknown")) %}
{% set news_score = read.get("news_impact", regime.get("news_impact", 0)) %}
{% set rotation_conf = rotation.get("confidence_score", rotation.get("confidence", "—")) %}
{% set risk_mode = shadow.get("risk_mode", shadow.get("mode", "Research")) %}

<section class="hero">
  <div>
    <div class="eyebrow">Research Mode · No Live Orders · Learning Interface</div>
    <h1>Ponder Invest AI</h1>
    <p class="muted">Follow the flow: market → scan → score → risk → rotate → shadow → learn → improve.</p>
  </div>
  <div class="hero-dog">
    <div class="dog-icon">🐕</div>
    <div>
      <strong>Ponder is watching.</strong>
      <p class="muted">Analyst only. Nothing adjusts live trades yet.</p>
    </div>
  </div>
</section>

<section class="card highlight">
  <h2>🧠 Current Decision</h2>
  <div class="roadmap-grid">
    <div><strong>State</strong><p>{{ regime_text }} · News {{ news_score }}/100 · Rotation {{ rotation_conf }}</p></div>
    <div><strong>Action</strong>
      {% if regime_text == "Risk-Off" or news_score|int >= 70 %}
      <p>Stay defensive. Study signals. Do not force entries.</p>
      {% else %}
      <p>Balanced mode. Only watch high-quality setups.</p>
      {% endif %}
    </div>
    <div><strong>Safety</strong><p>{{ risk_mode }} · Research-only · No live execution</p></div>
  </div>
</section>

<section class="card">
  <h2>🗺️ How The Bot Thinks</h2>
  <div class="roadmap-grid">
    <div><strong>1. Market Regime</strong><p>Decides if the environment is friendly or defensive.</p></div>
    <div><strong>2. Scanner</strong><p>Finds possible stocks or setups worth watching.</p></div>
    <div><strong>3. Scoring</strong><p>Ranks quality using trend, news, volume, analyst, and momentum.</p></div>
    <div><strong>4. Risk / Capital</strong><p>Checks if capital should be preserved or used.</p></div>
    <div><strong>5. Rotation / Sell</strong><p>Compares weak holdings against better opportunities.</p></div>
    <div><strong>6. Shadow Mode</strong><p>Simulates decisions before real automation.</p></div>
    <div><strong>7. Learning</strong><p>Tracks outcomes and learns what actually worked.</p></div>
    <div><strong>8. Next Upgrade</strong><p>Build one safe module at a time.</p></div>
  </div>
</section>

<section class="grid">
  <div class="card metric"><h3>Market Regime</h3><div class="big">{{ regime_text }}</div><p>Score: {{ read.get("regime_score", regime.get("score", "—")) }}</p></div>
  <div class="card metric"><h3>News Impact</h3><div class="big">{{ news_score }}</div><p>Higher = more defensive</p></div>
  <div class="card metric"><h3>Top Rotation</h3><div class="big small-big">{{ read.get("top_rotation", {}).get("move", "—") }}</div><p>Watch only unless confidence improves.</p></div>
  <div class="card metric"><h3>Alerts</h3><div class="big">{{ alerts_sum.get("total", 0) }}</div><p>{{ alerts_sum.get("critical", 0) }} critical · {{ alerts_sum.get("warning", 0) }} warnings</p></div>
</section>

<section class="split">
  <div class="card highlight">
    <h2>🧭 Ponder Says</h2>
    <ul>{% for item in ai.get("action_items", []) %}<li>{{ item }}</li>{% else %}<li>Wait for stronger setups.</li>{% endfor %}</ul>
  </div>
  <div class="card">
    <h2>📋 Easy Handoff</h2>
    <p>Need help later? Open <strong>Send to ChatGPT</strong> in the sidebar and paste the snapshot.</p>
    <p class="muted">This prevents guessing and makes upgrades safer.</p>
  </div>
</section>

<section class="grid">
  <div class="card"><h2>📊 Performance</h2><p>Win Rate: {{ performance.get("win_rate", "—") }}</p><p>Profit Factor: {{ performance.get("profit_factor", "—") }}</p></div>
  <div class="card"><h2>💰 Capital</h2><p>Used: {{ shadow.get("capital_used_pct", "—") }}</p><p>Free: {{ shadow.get("capital_free_pct", "—") }}</p></div>
  <div class="card"><h2>🔁 Rotation</h2><p>Confidence: {{ rotation_conf }}</p><p>Edge: {{ rotation.get("expected_edge", "—") }}</p></div>
  <div class="card"><h2>🚪 Sell</h2><p>Pressure: {{ sell.get("sell_pressure", "—") }}</p><p>Signal: {{ sell.get("decision", "—") }}</p></div>
</section>

{% endblock %}
''')

print("✅ Installed System Flow Map + Send to ChatGPT snapshot page")
print("Restart Flask, then open /debug-snapshot when you need to send context.")
