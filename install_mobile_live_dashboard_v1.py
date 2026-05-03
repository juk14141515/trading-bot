from pathlib import Path

ROOT = Path("/home/ubuntu/trading-bot")
APP = ROOT / "new_ponder_site/app.py"
DASH = ROOT / "new_ponder_site/templates/dashboard.html"
CSS = ROOT / "new_ponder_site/static/style.css"

DASH.with_suffix(".html.backup_mobile_live_v1").write_text(DASH.read_text())
APP.with_suffix(".py.backup_mobile_live_v1").write_text(APP.read_text())
CSS.with_suffix(".css.backup_mobile_live_v1").write_text(CSS.read_text())

app = APP.read_text()

if "def load_equity_history" not in app:
    app = app.replace(
'''def dashboard_data():
    return {''',
'''def load_equity_history():
    path = ROOT / "equity_history.csv"
    if not path.exists():
        return []
    try:
        import csv
        rows = []
        with path.open() as f:
            for row in csv.DictReader(f):
                rows.append(row)
        return rows[-80:]
    except Exception:
        return []


def dashboard_data():
    return {'''
    )

if '"equity": load_equity_history(),' not in app:
    app = app.replace(
        '"decisions": load_json("decision_engine_latest.json"),',
        '"decisions": load_json("decision_engine_latest.json"),\n        "equity": load_equity_history(),'
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
{% set decision_summary = decisions.get("summary", {}) %}
{% set sorted_decisions = decisions.get("decisions", []) | sort(attribute="score", reverse=True) %}
{% set best = sorted_decisions[0] if sorted_decisions else {} %}

{% set regime_text = read.get("regime", regime.get("regime", decisions.get("regime", "Unknown"))) %}
{% set news_score = read.get("news_impact", decisions.get("news_impact", 0)) %}
{% set buy_count = decision_summary.get("buy_count", 0) %}
{% set watch_count = decision_summary.get("watch_count", 0) %}
{% set ignore_count = decision_summary.get("ignore_count", 0) %}
{% set mode = "DEFENSIVE" if news_score|int >= 70 or regime_text == "Risk-Off" else "SELECTIVE" if buy_count == 0 else "OPPORTUNITY" %}

<section class="hero">
  <div>
    <div class="eyebrow">Personal Command Center · Research Mode · No Live Orders</div>
    <h1>Ponder Invest AI</h1>
    <p class="muted">Fast mobile-ready view: what matters, what to watch, and why Ponder is waiting.</p>
  </div>

  <div class="hero-dog">
    <div class="dog-icon">🐕</div>
    <div>
      <strong>Ponder is watching.</strong>
      <p class="muted">Mode: <span id="live-mode">{{ mode }}</span></p>
    </div>
  </div>
</section>

<section class="card brainline">
  <div>
    <div class="eyebrow">Instant Read</div>
    <h2 id="brainline">
      {% if mode == "DEFENSIVE" %}
        Ponder: Defensive conditions. No forced trades.
      {% elif mode == "SELECTIVE" %}
        Ponder: Watchlist active, but no strong buy signal yet.
      {% else %}
        Ponder: Opportunity detected. Validate before acting.
      {% endif %}
    </h2>
    <p class="muted">Last data update: <span id="updated-at">{{ decisions.get("updated_at", "—") }}</span></p>
  </div>
  <span class="mode-badge mode-{{ mode|lower }}">{{ mode }}</span>
</section>

<section class="grid">
  <div class="card metric">
    <h3>Market Regime</h3>
    <div class="big" id="regime">{{ regime_text }}</div>
    <p>Score: {{ read.get("regime_score", regime.get("score", "—")) }}</p>
  </div>

  <div class="card metric">
    <h3>News Risk</h3>
    <div class="big" id="news-risk">{{ news_score }}</div>
    <p>70+ usually means defensive.</p>
  </div>

  <div class="card metric">
    <h3>Buy Signals</h3>
    <div class="big" id="buy-count">{{ buy_count }}</div>
    <p>{{ watch_count }} watch · {{ ignore_count }} ignore</p>
  </div>

  <div class="card metric">
    <h3>Alerts</h3>
    <div class="big">{{ alerts_sum.get("total", 0) }}</div>
    <p>{{ alerts_sum.get("critical", 0) }} critical · {{ alerts_sum.get("warning", 0) }} warnings</p>
  </div>
</section>

<section class="card top-opportunity">
  <div>
    <div class="eyebrow">Top Opportunity</div>
    <h2>🏆 {{ best.get("symbol", "No setup yet") }}</h2>
    <p class="muted">{{ best.get("reason", "Run research pipeline to generate decisions.") }}</p>
    <div class="strength-wrap">
      <span>Strength</span>
      <div class="strength-track">
        <div class="strength-fill" style="width: {{ best.get("score", 0) }}%"></div>
      </div>
      <strong>{{ best.get("score", "—") }}</strong>
    </div>
  </div>

  <div class="opportunity-stats">
    {% set best_action = best.get("action", "none")|lower|replace(" ", "-")|replace("/", "") %}
    <div><strong>Action</strong><span class="pill action-{{ best_action }}">{{ best.get("action", "—") }}</span></div>
    <div><strong>Confidence</strong><span>{{ best.get("confidence", "—") }}</span></div>
    <div><strong>Score</strong><span>{{ best.get("score", "—") }}</span></div>
    <div><strong>Sell Pressure</strong><span>{{ best.get("sell_pressure", "—") }}</span></div>
  </div>
</section>

<section class="split">
  <div class="card highlight">
    <h2>🎯 Decision Feed</h2>
    <p class="muted">Ranked research-only decisions. Nothing here places trades.</p>

    <div class="decision-list compact">
      {% for d in sorted_decisions[:8] %}
        {% set action_class = d.get("action", "none")|lower|replace(" ", "-")|replace("/", "") %}
        <div class="decision-card decision-{{ action_class }}">
          <div class="decision-head">
            <strong>{{ d.get("symbol", "—") }}</strong>
            <span class="pill action-{{ action_class }}">{{ d.get("action", "—") }}</span>
          </div>
          <div class="decision-meta">
            <span>Conf: {{ d.get("confidence", "—") }}</span>
            <span>Score: {{ d.get("score", "—") }}</span>
            <span>Sell: {{ d.get("sell_pressure", "—") }}</span>
          </div>
          <p class="muted">{{ d.get("reason", "—") }}</p>
        </div>
      {% else %}
        <p>No decision data yet. Run research pipeline.</p>
      {% endfor %}
    </div>
  </div>

  <div class="card">
    <h2>🚫 Why No Trade?</h2>
    <ul>
      {% if news_score|int >= 70 %}<li>News risk is high at {{ news_score }}/100.</li>{% endif %}
      {% if buy_count == 0 %}<li>No BUY/STRONG_BUY signal passed the current filter.</li>{% endif %}
      {% if regime_text == "Risk-Off" %}<li>Market regime is defensive.</li>{% endif %}
      <li>Ponder is still research-only and protecting learning quality.</li>
    </ul>
  </div>
</section>

<section class="grid">
  <div class="card chart-card">
    <h2>📊 Decision Mix</h2>
    <canvas id="decisionChart" height="150"></canvas>
  </div>

  <div class="card chart-card">
    <h2>📈 Equity Snapshot</h2>
    <canvas id="equityChart" height="150"></canvas>
    <p class="muted">Uses equity_history.csv when available.</p>
  </div>

  <div class="card">
    <h2>⚙️ System Status</h2>
    <div class="readiness">
      <div><span class="dot warn"></span> Research-only mode</div>
      <div><span class="dot good"></span> Live dashboard refresh active</div>
      <div><span class="dot good"></span> Decision engine connected</div>
      <div><span class="dot risk"></span> Live execution disabled</div>
    </div>
  </div>

  <div class="card">
    <h2>📋 On-the-Go Rule</h2>
    <p><strong>Only care about three things:</strong></p>
    <p>Mode, Buy Signals, and Top Opportunity.</p>
    <p class="muted">Everything else is supporting evidence.</p>
  </div>
</section>

<script>
const initialData = {{ data | tojson }};

function drawBarChart(canvasId, values, labels) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width = canvas.offsetWidth;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  const max = Math.max(...values, 1);
  const gap = 14;
  const barW = (w - gap * (values.length + 1)) / values.length;

  values.forEach((v, i) => {
    const x = gap + i * (barW + gap);
    const bh = (v / max) * (h - 42);
    ctx.fillStyle = "rgba(167,139,250,.75)";
    ctx.fillRect(x, h - bh - 24, barW, bh);
    ctx.fillStyle = "#a7afc3";
    ctx.font = "12px system-ui";
    ctx.fillText(labels[i] + ": " + v, x, h - 6);
  });
}

function drawLineChart(canvasId, rows) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width = canvas.offsetWidth;
  const h = canvas.height;
  ctx.clearRect(0,0,w,h);

  const nums = (rows || []).map(r => Number(r.equity || r.account_equity || r.value || 0)).filter(Boolean);
  if (nums.length < 2) {
    ctx.fillStyle = "#a7afc3";
    ctx.font = "14px system-ui";
    ctx.fillText("Not enough equity history yet.", 12, 40);
    return;
  }

  const min = Math.min(...nums), max = Math.max(...nums);
  const range = Math.max(max - min, 1);
  ctx.strokeStyle = "rgba(167,139,250,.9)";
  ctx.lineWidth = 2;
  ctx.beginPath();

  nums.forEach((v, i) => {
    const x = (i / (nums.length - 1)) * (w - 20) + 10;
    const y = h - 20 - ((v - min) / range) * (h - 40);
    if (i === 0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
  });
  ctx.stroke();
}

function renderCharts(data) {
  const s = data.decisions?.summary || {};
  drawBarChart("decisionChart", [s.buy_count || 0, s.watch_count || 0, s.ignore_count || 0], ["Buy", "Watch", "Ignore"]);
  drawLineChart("equityChart", data.equity || []);
}

async function refreshLive() {
  try {
    const res = await fetch("/api/dashboard", { cache: "no-store" });
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("updated-at").textContent = data.decisions?.updated_at || "—";
    document.getElementById("regime").textContent = data.ai?.key_readout?.regime || data.regime?.regime || "—";
    document.getElementById("news-risk").textContent = data.ai?.key_readout?.news_impact || data.decisions?.news_impact || "—";
    document.getElementById("buy-count").textContent = data.decisions?.summary?.buy_count ?? "—";

    renderCharts(data);
  } catch (e) {
    console.log("Live refresh failed", e);
  }
}

renderCharts(initialData);
setInterval(refreshLive, 30000);
</script>

{% endblock %}
''')

css = CSS.read_text()
extra = r'''

/* ===== Mobile Live Dashboard v1 ===== */
.brainline {
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:18px;
  border-color:rgba(167,139,250,.55);
}

.brainline h2 {
  margin-bottom:8px;
}

.mode-badge {
  border:1px solid var(--line);
  border-radius:999px;
  padding:10px 14px;
  font-weight:900;
  letter-spacing:.08em;
}

.mode-defensive {
  color:var(--warn);
  border-color:rgba(245,208,76,.55);
  background:rgba(245,208,76,.08);
}

.mode-selective {
  color:var(--purple2);
  border-color:rgba(167,139,250,.55);
  background:rgba(167,139,250,.08);
}

.mode-opportunity {
  color:var(--good);
  border-color:rgba(142,233,154,.55);
  background:rgba(142,233,154,.08);
}

.strength-wrap {
  display:grid;
  grid-template-columns:auto 1fr auto;
  gap:12px;
  align-items:center;
  margin-top:18px;
  max-width:520px;
}

.strength-track {
  height:10px;
  border-radius:999px;
  background:rgba(255,255,255,.08);
  overflow:hidden;
  border:1px solid var(--line);
}

.strength-fill {
  height:100%;
  background:linear-gradient(90deg,var(--purple),var(--purple2));
}

.chart-card canvas {
  width:100%;
  background:rgba(255,255,255,.018);
  border:1px solid var(--line);
  border-radius:16px;
  padding:8px;
}

.decision-list.compact {
  grid-template-columns:1fr;
}

@media (max-width:850px) {
  .brainline {
    display:block;
  }

  .mode-badge {
    display:inline-flex;
    margin-top:14px;
  }
}
'''
if "Mobile Live Dashboard v1" not in css:
    css += extra
CSS.write_text(css)

print("✅ Installed mobile live dashboard v1")
