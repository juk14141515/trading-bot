from pathlib import Path

DASH = Path("new_ponder_site/templates/dashboard.html")
CSS = Path("new_ponder_site/static/style.css")

DASH.with_suffix(".html.backup_next_move_ai_v1").write_text(DASH.read_text())
CSS.with_suffix(".css.backup_next_move_ai_v1").write_text(CSS.read_text())

dash = DASH.read_text()

if '{% set deploy_threshold = 80 %}' not in dash:
    dash = dash.replace(
        '{% set readiness_gap = 85 - (best.get("score", 0)|float) %}',
        '''{% set readiness_gap = 85 - (best.get("score", 0)|float) %}
{% set deploy_threshold = 80 %}
{% set best_score = best.get("score", 0)|float %}
{% set deploy_decision = "DO NOT DEPLOY" if best_score < deploy_threshold or buy_count == 0 else "READY TO DEPLOY" %}
{% set ai_health = 90 if decisions.get("decisions") and capital.get("equity", 0)|float > 0 else 65 %}'''
    )

next_panel = r'''
<section class="card next-move-panel">
  <div class="next-left">
    <div class="eyebrow">Next Move</div>
    <h2>🧠 {{ deploy_decision }}</h2>
    <p class="muted">
      {% if deploy_decision == "DO NOT DEPLOY" %}
        Capital is available, but Ponder does not see enough edge yet.
      {% else %}
        Decision quality is strong enough to study possible deployment.
      {% endif %}
    </p>
  </div>

  <div class="next-grid">
    <div>
      <strong>Top Setup</strong>
      <span>{{ best.get("symbol", "—") }}</span>
      <small>{{ best.get("action", "—") }}</small>
    </div>
    <div>
      <strong>Score / Threshold</strong>
      <span>{{ best.get("score", "—") }} / {{ deploy_threshold }}</span>
      <small>{% if best_score < deploy_threshold %}Needs +{{ "%.1f"|format(deploy_threshold - best_score) }}{% else %}Passed{% endif %}</small>
    </div>
    <div>
      <strong>Deployable Capital</strong>
      <span>${{ "{:,.0f}".format(capital.get("deployable_cash", 0)|float) }}</span>
      <small>{{ capital.get("capital_mode", "UNKNOWN") }}</small>
    </div>
    <div>
      <strong>Rule</strong>
      <span>{% if deploy_decision == "DO NOT DEPLOY" %}WAIT{% else %}STUDY ENTRY{% endif %}</span>
      <small>Research-only</small>
    </div>
  </div>
</section>

<section class="card ai-overview">
  <div class="money-head">
    <div>
      <div class="eyebrow">AI System Health</div>
      <h2>🤖 Ponder System Overview</h2>
      <p class="muted">Checks whether capital, decisions, market context, and learning are working together.</p>
    </div>
    <div class="ai-score">{{ ai_health }}/100</div>
  </div>

  <div class="system-grid">
    <div><strong>Capital Engine</strong><span class="sys-good">↑ Online</span><small>{{ capital.get("capital_mode", "UNKNOWN") }}</small></div>
    <div><strong>Decision Engine</strong><span class="sys-good">↑ Active</span><small>{{ decisions.get("summary", {}).get("watch_count", 0) }} watch</small></div>
    <div><strong>Market Context</strong><span class="sys-warn">→ Cautious</span><small>News {{ news_score }}/100</small></div>
    <div><strong>Learning</strong><span class="sys-warn">→ Collecting</span><small>Research-only</small></div>
  </div>
</section>
'''

if "next-move-panel" not in dash:
    dash = dash.replace('<section class="card brainline">', next_panel + '\n<section class="card brainline">')

# Add IDs/classes for live updating and colorblind markers
dash = dash.replace(
    '<div class="mode-badge mode-selective">{{ capital.get("capital_mode", "UNKNOWN") }}</div>',
    '<div class="mode-badge mode-selective" id="capital-mode-badge">{{ capital.get("capital_mode", "UNKNOWN") }}</div>'
)

dash = dash.replace(
    '<p class="muted" id="money-next">{{ capital.get("next_money_action", "Run capital intelligence to load account data.") }}</p>',
    '<p class="muted money-next-live" id="money-next">{{ capital.get("next_money_action", "Run capital intelligence to load account data.") }}</p>'
)

# Patch JS money render with arrows
dash = dash.replace(
'''todayEl.textContent = fmtMoney(c.today_pl);
  todayEl.style.color = c.today_pl > 0 ? "#8ee99a" : c.today_pl < 0 ? "#ff6b7a" : "#eef2ff";''',
'''todayEl.textContent = (c.today_pl > 0 ? "↑ " : c.today_pl < 0 ? "↓ " : "→ ") + fmtMoney(c.today_pl);
  todayEl.style.color = c.today_pl > 0 ? "#8ee99a" : c.today_pl < 0 ? "#ff6b7a" : "#eef2ff";'''
)

dash = dash.replace(
'''weekEl.textContent = fmtMoney(c.week_pl);
  weekEl.style.color = c.week_pl > 0 ? "#8ee99a" : c.week_pl < 0 ? "#ff6b7a" : "#eef2ff";''',
'''weekEl.textContent = (c.week_pl > 0 ? "↑ " : c.week_pl < 0 ? "↓ " : "→ ") + fmtMoney(c.week_pl);
  weekEl.style.color = c.week_pl > 0 ? "#8ee99a" : c.week_pl < 0 ? "#ff6b7a" : "#eef2ff";'''
)

dash = dash.replace(
'''allEl.textContent = fmtMoney(c.all_time_pl);
  allEl.style.color = c.all_time_pl > 0 ? "#8ee99a" : c.all_time_pl < 0 ? "#ff6b7a" : "#eef2ff";''',
'''allEl.textContent = (c.all_time_pl > 0 ? "↑ " : c.all_time_pl < 0 ? "↓ " : "→ ") + fmtMoney(c.all_time_pl);
  allEl.style.color = c.all_time_pl > 0 ? "#8ee99a" : c.all_time_pl < 0 ? "#ff6b7a" : "#eef2ff";'''
)

dash = dash.replace(
'''document.getElementById("money-next").textContent = c.next_money_action || "";''',
'''document.getElementById("money-next").textContent = c.next_money_action || "";
  const modeBadge = document.getElementById("capital-mode-badge");
  if (modeBadge) modeBadge.textContent = c.capital_mode || "UNKNOWN";'''
)

DASH.write_text(dash)

css = CSS.read_text()
if "Next Move AI Overview v1" not in css:
    css += r'''

/* ===== Next Move AI Overview v1 ===== */
.next-move-panel {
  display:grid;
  grid-template-columns:1fr 2fr;
  gap:22px;
  align-items:center;
  border-color:rgba(167,139,250,.55);
  background:
    radial-gradient(circle at top left, rgba(167,139,250,.16), transparent 34%),
    linear-gradient(180deg,var(--card),#090d15);
}

.next-move-panel h2 {
  font-size:34px;
}

.next-grid,
.system-grid {
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:12px;
}

.next-grid div,
.system-grid div {
  border:1px solid var(--line);
  border-radius:16px;
  padding:14px;
  background:rgba(255,255,255,.025);
}

.next-grid strong,
.system-grid strong {
  display:block;
  color:var(--muted);
  text-transform:uppercase;
  letter-spacing:.08em;
  font-size:12px;
  margin-bottom:8px;
}

.next-grid span,
.system-grid span {
  display:block;
  font-size:20px;
  font-weight:900;
}

.next-grid small,
.system-grid small {
  display:block;
  margin-top:6px;
  color:var(--muted);
}

.ai-overview {
  border-color:rgba(142,233,154,.35);
}

.ai-score {
  font-size:34px;
  font-weight:900;
  border:1px solid rgba(142,233,154,.45);
  color:var(--good);
  border-radius:18px;
  padding:14px 18px;
  background:rgba(142,233,154,.08);
}

.sys-good { color:var(--good); }
.sys-warn { color:var(--warn); }
.sys-bad { color:var(--bad); }

.money-next-live {
  margin-top:18px;
  font-size:18px;
  font-weight:800;
}

@media (max-width:1100px) {
  .next-move-panel {
    grid-template-columns:1fr;
  }
  .next-grid,
  .system-grid {
    grid-template-columns:repeat(2,minmax(0,1fr));
  }
}

@media (max-width:700px) {
  .next-grid,
  .system-grid {
    grid-template-columns:1fr;
  }
}
'''
CSS.write_text(css)

print("✅ Installed Next Move Panel + AI Overview + accessible P/L arrows.")
