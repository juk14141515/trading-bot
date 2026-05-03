from pathlib import Path

ROOT = Path("/home/ubuntu/trading-bot")
APP = ROOT / "new_ponder_site/app.py"
DASH = ROOT / "new_ponder_site/templates/dashboard.html"

# Backup
backup = DASH.with_suffix(".html.backup_clean_decision_feed_v1")
backup.write_text(DASH.read_text())

# Ensure app loads decision data
app = APP.read_text()
if '"decisions": load_json("decision_engine_latest.json")' not in app:
    app = app.replace(
        '"achievements": load_json("achievements_latest.json"),',
        '"achievements": load_json("achievements_latest.json"),\n        "decisions": load_json("decision_engine_latest.json"),'
    )
APP.write_text(app)

DASH.write_text('''{% extends "base.html" %}
{% block content %}

{% set ai = data.get("ai", {}) %}
{% set alerts = data.get("alerts", {}) %}
{% set rotation = data.get("rotation", {}) %}
{% set regime = data.get("regime", {}) %}
{% set decisions = data.get("decisions", {}) %}
{% set read = ai.get("key_readout", {}) %}
{% set alerts_sum = alerts.get("summary", {}) %}

{% set regime_text = read.get("regime", regime.get("regime", decisions.get("regime", "Unknown"))) %}
{% set news_score = read.get("news_impact", decisions.get("news_impact", "—")) %}
{% set top_rotation = read.get("top_rotation", {}) %}
{% set decision_summary = decisions.get("summary", {}) %}

<section class="hero">
  <div>
    <div class="eyebrow">Research Mode · No Live Orders · Clean Command Center</div>
    <h1>Ponder Invest AI</h1>
    <p class="muted">
      Main dashboard answers one question: what is the system thinking right now?
    </p>
  </div>

  <div class="hero-dog">
    <div class="dog-icon">🐕</div>
    <div>
      <strong>Ponder is watching.</strong>
      <p class="muted">Analyst only. No live execution.</p>
    </div>
  </div>
</section>

<section class="grid">
  <div class="card metric">
    <h3>Market Regime</h3>
    <div class="big">{{ regime_text }}</div>
    <p>Score: {{ read.get("regime_score", regime.get("score", "—")) }}</p>
  </div>

  <div class="card metric">
    <h3>News Risk</h3>
    <div class="big">{{ news_score }}</div>
    <p>Higher = more defensive</p>
  </div>

  <div class="card metric">
    <h3>Top Rotation</h3>
    <div class="big small-big">{{ top_rotation.get("move", "—") }}</div>
    <p>{{ top_rotation.get("action", "Research only") }}</p>
  </div>

  <div class="card metric">
    <h3>Alerts</h3>
    <div class="big">{{ alerts_sum.get("total", 0) }}</div>
    <p>{{ alerts_sum.get("critical", 0) }} critical · {{ alerts_sum.get("warning", 0) }} warnings</p>
  </div>
</section>

<section class="card highlight">
  <h2>🎯 Decision Feed</h2>
  <p class="muted">Research-only decisions from Decision Engine. These do not place trades.</p>

  <div class="roadmap-grid">
    <div><strong>Buy Signals</strong><p>{{ decision_summary.get("buy_count", 0) }}</p></div>
    <div><strong>Watch</strong><p>{{ decision_summary.get("watch_count", 0) }}</p></div>
    <div><strong>Ignore</strong><p>{{ decision_summary.get("ignore_count", 0) }}</p></div>
  </div>

  <div class="decision-list">
    {% for d in decisions.get("decisions", [])[:10] %}
      <div class="card mini">
        <h3>{{ d.get("symbol", "—") }} · {{ d.get("action", "—") }}</h3>
        <p><strong>Confidence:</strong> {{ d.get("confidence", "—") }}</p>
        <p><strong>Score:</strong> {{ d.get("score", "—") }} · <strong>Sell Pressure:</strong> {{ d.get("sell_pressure", "—") }}</p>
        <p class="muted">{{ d.get("reason", "—") }}</p>
      </div>
    {% else %}
      <p>No decision data yet. Run <code>python3 research_pipeline_v1.py</code>.</p>
    {% endfor %}
  </div>
</section>

<section class="split">
  <div class="card">
    <h2>🧠 Ponder Summary</h2>
    <ul>
      {% for item in ai.get("plain_english_summary", [])[:5] %}
        <li>{{ item }}</li>
      {% else %}
        <li>No plain-English summary yet.</li>
      {% endfor %}
    </ul>
  </div>

  <div class="card">
    <h2>⚙️ System Status</h2>
    <div class="readiness">
      <div><span class="dot warn"></span> Research-only mode</div>
      <div><span class="dot good"></span> Decision feed active</div>
      <div><span class="dot good"></span> Learning data collecting</div>
      <div><span class="dot risk"></span> Live execution disabled</div>
    </div>
  </div>
</section>

<section class="card">
  <h2>🗺️ How This Flows</h2>
  <div class="roadmap-grid">
    <div><strong>1. Market</strong><p>Regime + news risk define environment.</p></div>
    <div><strong>2. Scanner</strong><p>Finds possible opportunities.</p></div>
    <div><strong>3. Decision</strong><p>Turns scores into WATCH / BUY / IGNORE.</p></div>
    <div><strong>4. Learning</strong><p>Tracks outcomes before automation.</p></div>
  </div>
</section>

{% endblock %}
''')

print("✅ Refactored dashboard clean version with Decision Feed UI")
print("Backup saved:", backup)
