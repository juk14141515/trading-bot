from pathlib import Path

DASH = Path("new_ponder_site/templates/dashboard.html")
CSS = Path("new_ponder_site/static/style.css")

DASH.with_suffix(".html.backup_action_bias_v1").write_text(DASH.read_text())
CSS.with_suffix(".css.backup_action_bias_v1").write_text(CSS.read_text())

dash = DASH.read_text()

dash = dash.replace(
'''{% set mode = "DEFENSIVE" if news_score|int >= 70 or regime_text == "Risk-Off" else "SELECTIVE" if buy_count == 0 else "OPPORTUNITY" %}''',
'''{% set mode = "DEFENSIVE" if news_score|int >= 70 or regime_text == "Risk-Off" else "SELECTIVE" if buy_count == 0 else "OPPORTUNITY" %}
{% set action_bias = "WAIT" if buy_count == 0 else "LOOK FOR ENTRY" %}
{% set pressure = "LOW" if buy_count == 0 and watch_count < 5 else "MEDIUM" if watch_count >= 4 else "HIGH" %}
{% set readiness_gap = 85 - (best.get("score", 0)|float) %}'''
)

dash = dash.replace(
'''<p class="muted">Last data update: <span id="updated-at">{{ decisions.get("updated_at", "—") }}</span></p>''',
'''<p class="muted">Last data update: <span id="updated-at">{{ decisions.get("updated_at", "—") }}</span></p>
    <div class="quick-bias">
      <span>Action Bias: <strong>{{ action_bias }}</strong></span>
      <span>Opportunity Pressure: <strong>{{ pressure }}</strong></span>
      <span>Trade Readiness: <strong>{{ best.get("score", "—") }}/85</strong></span>
    </div>'''
)

dash = dash.replace(
'''<strong>{{ best.get("score", "—") }}</strong>''',
'''<strong>{{ best.get("score", "—") }}</strong>
      <small class="muted">{% if readiness_gap > 0 %}Needs +{{ "%.1f"|format(readiness_gap) }}{% else %}Ready{% endif %}</small>'''
)

DASH.write_text(dash)

css = CSS.read_text()
css += r'''

/* ===== Action Bias UI v1 ===== */
.quick-bias {
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  margin-top:16px;
}

.quick-bias span {
  border:1px solid var(--line);
  border-radius:999px;
  padding:8px 12px;
  background:rgba(255,255,255,.035);
  color:var(--muted);
}

.quick-bias strong {
  color:var(--text);
}
'''
CSS.write_text(css)

print("✅ Added action bias, opportunity pressure, and readiness gap.")
