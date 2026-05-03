from pathlib import Path

file_path = Path("new_ponder_site/templates/dashboard.html")

new_content = """{% extends "base.html" %}
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

<section class="hero">
  <div>
    <div class="eyebrow">Research Mode · No Live Orders · Modular Command Center</div>
    <h1>Ponder Invest AI</h1>
    <p class="muted">
      Decision engine for market intelligence, capital discipline, and adaptive learning.
    </p>
  </div>

  <div class="hero-dog">
    <div class="dog-icon">🐕</div>
    <div>
      <strong>Ponder is watching.</strong>
      <p class="muted">Risk first. Patience over forced trades.</p>
    </div>
  </div>
</section>

<!-- 🧠 DECISION LAYER -->
<section class="card highlight">
  <h2>🧠 Ponder Decision Layer</h2>

  {% set regime_text = read.get("regime", regime.get("regime", "Unknown")) %}
  {% set news_score = read.get("news_impact", regime.get("news_impact", 0)) %}
  {% set rotation_conf = rotation.get("confidence_score", rotation.get("confidence", "—")) %}
  {% set risk_mode = shadow.get("risk_mode", shadow.get("mode", "Research")) %}

  <div class="roadmap-grid">
    <div>
      <strong>Current State</strong>
      <p>{{ regime_text }} · News: {{ news_score }} · Rotation: {{ rotation_conf }}</p>
    </div>

    <div>
      <strong>Recommended Action</strong>
      {% if regime_text == "Risk-Off" or news_score|int >= 70 %}
        <p>Stay defensive. Do NOT deploy capital.</p>
      {% else %}
        <p>Balanced mode. Only take high-quality setups.</p>
      {% endif %}
    </div>

    <div>
      <strong>Capital Mode</strong>
      <p>{{ risk_mode }} · Research-only · No execution</p>
    </div>
  </div>
</section>

<!-- 📊 METRICS -->
<section class="grid">
  <div class="card metric">
    <h3>Market Regime</h3>
    <div class="big">{{ regime_text }}</div>
    <p>Score: {{ read.get("regime_score", regime.get("score", "—")) }}</p>
  </div>

  <div class="card metric">
    <h3>News Impact</h3>
    <div class="big">{{ news_score }}</div>
    <p>Higher = defensive</p>
  </div>

  <div class="card metric">
    <h3>Top Rotation</h3>
    <div class="big small-big">
      {{ read.get("top_rotation", {}).get("move", "—") }}
    </div>
  </div>

  <div class="card metric">
    <h3>Alerts</h3>
    <div class="big">{{ alerts_sum.get("total", 0) }}</div>
  </div>
</section>

<!-- 🧭 ACTION -->
<section class="split">
  <div class="card highlight">
    <h2>🧭 Ponder Says</h2>
    <ul>
      {% for item in ai.get("action_items", []) %}
        <li>{{ item }}</li>
      {% else %}
        <li>Wait for stronger setups.</li>
      {% endfor %}
    </ul>
  </div>

  <div class="card">
    <h2>🔐 Safety</h2>
    <div class="readiness">
      <div><span class="dot warn"></span> Research mode</div>
      <div><span class="dot risk"></span> No live trading</div>
      <div><span class="dot good"></span> Data collection active</div>
    </div>
  </div>
</section>

<!-- 📈 INTELLIGENCE -->
<section class="grid">
  <div class="card">
    <h2>📊 Performance</h2>
    <p>Win Rate: {{ performance.get("win_rate", "—") }}</p>
    <p>Profit Factor: {{ performance.get("profit_factor", "—") }}</p>
  </div>

  <div class="card">
    <h2>💰 Capital</h2>
    <p>Used: {{ shadow.get("capital_used_pct", "—") }}</p>
    <p>Free: {{ shadow.get("capital_free_pct", "—") }}</p>
  </div>

  <div class="card">
    <h2>🔁 Rotation</h2>
    <p>Confidence: {{ rotation_conf }}</p>
    <p>Edge: {{ rotation.get("expected_edge", "—") }}</p>
  </div>

  <div class="card">
    <h2>🚪 Sell</h2>
    <p>Pressure: {{ sell.get("sell_pressure", "—") }}</p>
    <p>Signal: {{ sell.get("decision", "—") }}</p>
  </div>
</section>

{% endblock %}
"""

file_path.write_text(new_content)

print("✅ Dashboard upgraded to Command Center v2")
