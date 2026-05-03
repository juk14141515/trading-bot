from pathlib import Path

ROOT = Path("/home/ubuntu/trading-bot")
DASH = ROOT / "new_ponder_site/templates/dashboard.html"
CSS = ROOT / "new_ponder_site/static/style.css"

# Backups
DASH.with_suffix(".html.backup_decision_ui_v2").write_text(DASH.read_text())
CSS.with_suffix(".css.backup_decision_ui_v2").write_text(CSS.read_text())

dash = DASH.read_text()

# Add sorted decisions + best opportunity variables
if '{% set sorted_decisions = decisions.get("decisions", []) | sort(attribute="score", reverse=True) %}' not in dash:
    dash = dash.replace(
        '{% set decision_summary = decisions.get("summary", {}) %}',
        '''{% set decision_summary = decisions.get("summary", {}) %}
{% set sorted_decisions = decisions.get("decisions", []) | sort(attribute="score", reverse=True) %}
{% set best = sorted_decisions[0] if sorted_decisions else {} %}'''
    )

top_opportunity = '''
<section class="card top-opportunity">
  <div>
    <div class="eyebrow">Top Opportunity</div>
    <h2>🏆 {{ best.get("symbol", "No setup yet") }}</h2>
    <p class="muted">{{ best.get("reason", "Run research pipeline to generate decisions.") }}</p>
  </div>

  <div class="opportunity-stats">
    <div><strong>Action</strong><span class="pill action-{{ best.get("action", "none")|lower|replace(" ", "-")|replace("/", "") }}">{{ best.get("action", "—") }}</span></div>
    <div><strong>Confidence</strong><span>{{ best.get("confidence", "—") }}</span></div>
    <div><strong>Score</strong><span>{{ best.get("score", "—") }}</span></div>
    <div><strong>Sell Pressure</strong><span>{{ best.get("sell_pressure", "—") }}</span></div>
  </div>
</section>
'''

if "top-opportunity" not in dash:
    dash = dash.replace('<section class="card highlight">\n  <h2>🎯 Decision Feed</h2>', top_opportunity + '\n<section class="card highlight">\n  <h2>🎯 Decision Feed</h2>')

# Replace decision loop with sorted + colored rows
old_loop = '''{% for d in decisions.get("decisions", [])[:10] %}
      <div class="card mini">
        <h3>{{ d.get("symbol", "—") }} · {{ d.get("action", "—") }}</h3>
        <p><strong>Confidence:</strong> {{ d.get("confidence", "—") }}</p>
        <p><strong>Score:</strong> {{ d.get("score", "—") }} · <strong>Sell Pressure:</strong> {{ d.get("sell_pressure", "—") }}</p>
        <p class="muted">{{ d.get("reason", "—") }}</p>
      </div>
    {% else %}'''

new_loop = '''{% for d in sorted_decisions[:10] %}
      {% set action_class = d.get("action", "none")|lower|replace(" ", "-")|replace("/", "") %}
      <div class="decision-card decision-{{ action_class }}">
        <div class="decision-head">
          <strong>{{ d.get("symbol", "—") }}</strong>
          <span class="pill action-{{ action_class }}">{{ d.get("action", "—") }}</span>
        </div>
        <div class="decision-meta">
          <span>Confidence: {{ d.get("confidence", "—") }}</span>
          <span>Score: {{ d.get("score", "—") }}</span>
          <span>Sell Pressure: {{ d.get("sell_pressure", "—") }}</span>
        </div>
        <p class="muted">{{ d.get("reason", "—") }}</p>
      </div>
    {% else %}'''

dash = dash.replace(old_loop, new_loop)
DASH.write_text(dash)

css_add = r'''

/* ===== Decision Feed Upgrade v2 ===== */
.top-opportunity {
  display:flex;
  justify-content:space-between;
  gap:24px;
  align-items:center;
  border-color:rgba(139,92,246,.55);
  background:
    radial-gradient(circle at top left, rgba(139,92,246,.18), transparent 32%),
    linear-gradient(180deg,var(--card),#090d15);
}

.opportunity-stats {
  display:grid;
  grid-template-columns:repeat(4,minmax(90px,1fr));
  gap:12px;
  min-width:520px;
}

.opportunity-stats div {
  border:1px solid var(--line);
  border-radius:16px;
  padding:14px;
  background:rgba(255,255,255,.025);
}

.opportunity-stats strong {
  display:block;
  font-size:12px;
  text-transform:uppercase;
  letter-spacing:.08em;
  color:var(--muted);
  margin-bottom:8px;
}

.opportunity-stats span {
  font-weight:900;
  font-size:18px;
}

.decision-list {
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:14px;
  margin-top:18px;
}

.decision-card {
  border:1px solid var(--line);
  border-radius:18px;
  padding:18px;
  background:rgba(255,255,255,.025);
}

.decision-head {
  display:flex;
  justify-content:space-between;
  gap:12px;
  align-items:center;
  margin-bottom:12px;
  font-size:20px;
}

.decision-meta {
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  color:var(--muted);
  font-size:14px;
}

.pill {
  display:inline-flex;
  align-items:center;
  border-radius:999px;
  padding:6px 10px;
  font-size:12px !important;
  font-weight:900;
  letter-spacing:.04em;
  border:1px solid var(--line);
}

.action-buy,
.action-strong_buy {
  color:var(--good);
  border-color:rgba(142,233,154,.55);
  background:rgba(142,233,154,.09);
}

.action-watch,
.action-wait,
.action-wait_pullback {
  color:var(--warn);
  border-color:rgba(245,208,76,.55);
  background:rgba(245,208,76,.09);
}

.action-ignore,
.action-none {
  color:var(--muted);
  border-color:rgba(167,175,195,.35);
  background:rgba(167,175,195,.06);
}

.action-exit-avoid {
  color:var(--bad);
  border-color:rgba(255,107,122,.55);
  background:rgba(255,107,122,.09);
}

.decision-buy,
.decision-strong_buy {
  border-left:4px solid var(--good);
}

.decision-watch,
.decision-wait,
.decision-wait_pullback {
  border-left:4px solid var(--warn);
}

.decision-ignore {
  border-left:4px solid #4b5563;
}

.decision-exit-avoid {
  border-left:4px solid var(--bad);
}

@media (max-width:1100px) {
  .top-opportunity {
    display:block;
  }

  .opportunity-stats {
    min-width:0;
    grid-template-columns:repeat(2,minmax(0,1fr));
    margin-top:18px;
  }

  .decision-list {
    grid-template-columns:1fr;
  }
}
'''

css = CSS.read_text()
if "Decision Feed Upgrade v2" not in css:
    css += css_add
CSS.write_text(css)

print("✅ Added top opportunity, sorted decision feed, and color-coded actions.")
