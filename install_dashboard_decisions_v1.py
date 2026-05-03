from pathlib import Path

ROOT = Path("/home/ubuntu/trading-bot")
APP = ROOT / "new_ponder_site/app.py"
DASH = ROOT / "new_ponder_site/templates/dashboard.html"

# Patch app.py to load decision JSON
app = APP.read_text()
if '"decisions": load_json("decision_engine_latest.json")' not in app:
    app = app.replace(
        '"achievements": load_json("achievements_latest.json"),',
        '"achievements": load_json("achievements_latest.json"),\n        "decisions": load_json("decision_engine_latest.json"),'
    )
APP.write_text(app)

dash = DASH.read_text()

# Add decisions variable
if '{% set decisions = data.get("decisions", {}) %}' not in dash:
    dash = dash.replace(
        '{% set achievements = data.get("achievements", {}) %}',
        '{% set achievements = data.get("achievements", {}) %}\n{% set decisions = data.get("decisions", {}) %}'
    )

decision_panel = '''
<section class="card highlight">
  <h2>🎯 Trade Decisions</h2>
  <p class="muted">
    Research-only recommendations from Decision Engine v1. These do not place trades.
  </p>

  <div class="roadmap-grid">
    <div>
      <strong>Buy Signals</strong>
      <p>{{ decisions.get("summary", {}).get("buy_count", "—") }}</p>
    </div>
    <div>
      <strong>Watchlist</strong>
      <p>{{ decisions.get("summary", {}).get("watch_count", "—") }}</p>
    </div>
    <div>
      <strong>Ignored</strong>
      <p>{{ decisions.get("summary", {}).get("ignore_count", "—") }}</p>
    </div>
  </div>

  <div class="decision-list">
    {% for d in decisions.get("decisions", [])[:8] %}
      <div class="decision-row">
        <strong>{{ d.get("symbol", "—") }}</strong>
        <span>{{ d.get("action", "—") }}</span>
        <span>{{ d.get("confidence", "—") }}</span>
        <p>{{ d.get("reason", "—") }}</p>
      </div>
    {% else %}
      <p>No decision data yet. Run research_pipeline_v1.py.</p>
    {% endfor %}
  </div>
</section>
'''

# Insert before metrics
if "🎯 Trade Decisions" not in dash:
    dash = dash.replace("<!-- 📊 METRICS -->", decision_panel + "\n\n<!-- 📊 METRICS -->")

DASH.write_text(dash)

print("✅ Dashboard decisions panel installed.")
