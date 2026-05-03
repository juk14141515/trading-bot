from pathlib import Path

ROOT = Path("/home/ubuntu/trading-bot")
DASH = ROOT / "new_ponder_site/templates/dashboard.html"

html = DASH.read_text()

insert_after = '''</section>

<section class="grid">
  <div class="card metric">'''

decision_layer = '''</section>

<section class="card highlight">
  <h2>🧠 Ponder Decision Layer</h2>

  {% set regime_text = read.get("regime", regime.get("regime", "Unknown")) %}
  {% set news_score = read.get("news_impact", regime.get("news_impact", 0)) %}
  {% set rotation_conf = rotation.get("confidence_score", rotation.get("confidence", "—")) %}
  {% set risk_mode = shadow.get("risk_mode", shadow.get("mode", "Research")) %}

  <div class="roadmap-grid">
    <div>
      <strong>Current State</strong>
      <p>{{ regime_text }} · News Impact: {{ news_score }} · Rotation Confidence: {{ rotation_conf }}</p>
    </div>

    <div>
      <strong>Recommended Action</strong>
      {% if regime_text == "Risk-Off" or news_score|int >= 70 %}
        <p>Stay defensive. Do not force entries. Let research data collect.</p>
      {% else %}
        <p>Balanced mode. Watch only high-quality setups and avoid weak rotations.</p>
      {% endif %}
    </div>

    <div>
      <strong>Capital Mode</strong>
      <p>{{ risk_mode }} · Live trading disabled · Research-only validation active.</p>
    </div>
  </div>
</section>

<section class="grid">
  <div class="card metric">'''

if "Ponder Decision Layer" not in html:
    html = html.replace(insert_after, decision_layer, 1)

DASH.write_text(html)
print("✅ Installed Ponder Decision Layer v1")
print("Updated:", DASH)
