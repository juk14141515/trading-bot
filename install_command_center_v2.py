from pathlib import Path

ROOT = Path("/home/ubuntu/trading-bot")
SITE = ROOT / "new_ponder_site"
TEMPLATES = SITE / "templates"

APP = r'''from flask import Flask, render_template, jsonify, request, Response
import json
import os
from pathlib import Path
from functools import wraps

app = Flask(__name__)

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "static" / "research"


def load_json(name):
    path = RESEARCH / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as e:
        return {"error": str(e), "file": name}


def dashboard_data():
    return {
        "ai": load_json("ai_summary_latest.json"),
        "alerts": load_json("notifications_latest.json"),
        "market": load_json("market_intelligence_latest.json"),
        "overnight": load_json("overnight_brief_latest.json"),
        "sell": load_json("sell_intelligence_latest.json"),
        "rotation": load_json("rotation_engine_latest.json"),
        "performance": load_json("rotation_performance_latest.json"),
        "shadow": load_json("shadow_capital_allocator_latest.json"),
        "regime": load_json("market_regime_filter_latest.json"),
        "assistant": load_json("ponder_assistant_latest.json"),
        "achievements": load_json("achievements_latest.json"),
    }


def auth_enabled():
    return bool(os.getenv("DASHBOARD_USER") and os.getenv("DASHBOARD_PASS"))


def check_auth(username, password):
    return (
        username == os.getenv("DASHBOARD_USER")
        and password == os.getenv("DASHBOARD_PASS")
    )


def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not auth_enabled():
            return fn(*args, **kwargs)

        auth = request.authorization
        if auth and check_auth(auth.username, auth.password):
            return fn(*args, **kwargs)

        return Response(
            "Login required",
            401,
            {"WWW-Authenticate": 'Basic realm="Ponder Invest AI"'},
        )

    return wrapper


@app.route("/")
@auth_required
def dashboard():
    return render_template("dashboard.html", data=dashboard_data())


@app.route("/research")
@auth_required
def research():
    return render_template("research.html", data=dashboard_data())


@app.route("/assistant")
@auth_required
def assistant():
    data = dashboard_data()
    return render_template("assistant.html", ai=data["ai"], assistant=data["assistant"])


@app.route("/learning")
@auth_required
def learning():
    data = dashboard_data()
    return render_template(
        "learning.html",
        achievements=data["achievements"],
        performance=data["performance"],
    )


@app.route("/settings")
@auth_required
def settings():
    return render_template("settings.html")


@app.route("/api/dashboard")
@auth_required
def api_dashboard():
    return jsonify(dashboard_data())


@app.route("/health")
def health():
    return {
        "status": "ok",
        "site": "new_ponder_site",
        "research_path": str(RESEARCH),
        "auth_enabled": auth_enabled(),
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
'''

DASHBOARD = r'''{% extends "base.html" %}
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

<section class="hero pro-hero">
  <div>
    <div class="eyebrow">Research Mode · No Live Orders · Modular Command Center</div>
    <h1>Ponder Invest AI</h1>
    <p class="muted">
      A professional black-theme control center for market intelligence, capital discipline,
      learning, alerts, achievements, and future safe automation.
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

<section class="grid">
  <div class="card metric">
    <h3>Market Regime</h3>
    <div class="big">{{ read.get("regime", regime.get("regime", "—")) }}</div>
    <p>Score: {{ read.get("regime_score", regime.get("score", "—")) }}</p>
  </div>

  <div class="card metric">
    <h3>News Impact</h3>
    <div class="big">{{ read.get("news_impact", regime.get("news_impact", "—")) }}</div>
    <p>Higher = more defensive</p>
  </div>

  <div class="card metric">
    <h3>Top Rotation</h3>
    <div class="big small-big">
      {{ read.get("top_rotation", {}).get("move", rotation.get("top_rotation", "—")) }}
    </div>
    <p>{{ read.get("top_rotation", {}).get("action", rotation.get("decision", "")) }}</p>
  </div>

  <div class="card metric">
    <h3>Alerts</h3>
    <div class="big">{{ alerts_sum.get("total", 0) }}</div>
    <p>{{ alerts_sum.get("critical", 0) }} critical · {{ alerts_sum.get("warning", 0) }} warnings</p>
  </div>
</section>

<section class="split">
  <div class="card highlight">
    <h2>🧭 Ponder Says</h2>
    <ul>
      {% for item in ai.get("action_items", []) %}
        <li>{{ item }}</li>
      {% else %}
        <li>Review AI Summary, Alerts, Rotation, Sell Intelligence, and Capital before changing anything.</li>
      {% endfor %}
    </ul>
  </div>

  <div class="card">
    <h2>🔐 Security + Safety</h2>
    <div class="readiness">
      <div><span class="dot warn"></span> Research-only mode</div>
      <div><span class="dot risk"></span> Live automation disabled</div>
      <div><span class="dot good"></span> Login protection available through .env</div>
      <div><span class="dot good"></span> Bot execution untouched</div>
    </div>
  </div>
</section>

<section class="grid">
  <div class="card">
    <h2>📊 Performance</h2>
    <p><strong>Win Rate:</strong> {{ performance.get("win_rate", performance.get("overall_win_rate", "—")) }}</p>
    <p><strong>Profit Factor:</strong> {{ performance.get("profit_factor", "—") }}</p>
    <p><strong>Drawdown:</strong> {{ performance.get("max_drawdown", performance.get("drawdown", "—")) }}</p>
    <p><strong>Rotation Accuracy:</strong> {{ performance.get("rotation_accuracy", "—") }}</p>
  </div>

  <div class="card">
    <h2>💰 Capital Efficiency</h2>
    <p><strong>Capital Used:</strong> {{ shadow.get("capital_used_pct", shadow.get("used_capital_pct", "—")) }}</p>
    <p><strong>Free Capital:</strong> {{ shadow.get("capital_free_pct", shadow.get("free_capital_pct", "—")) }}</p>
    <p><strong>Efficiency Score:</strong> {{ shadow.get("capital_efficiency_score", shadow.get("efficiency_score", "—")) }}</p>
    <p><strong>Mode:</strong> {{ shadow.get("risk_mode", shadow.get("mode", "Research")) }}</p>
  </div>

  <div class="card">
    <h2>🔁 Rotation Intelligence</h2>
    <p><strong>Confidence:</strong> {{ rotation.get("confidence_score", rotation.get("confidence", "—")) }}</p>
    <p><strong>Expected Edge:</strong> {{ rotation.get("expected_edge", "—") }}</p>
    <p><strong>Best Signal:</strong> {{ rotation.get("best_signal", "—") }}</p>
    <p><strong>Status:</strong> {{ rotation.get("status", rotation.get("summary", "Monitoring")) }}</p>
  </div>

  <div class="card">
    <h2>🚪 Sell Intelligence</h2>
    <p><strong>Sell Pressure:</strong> {{ sell.get("sell_pressure", sell.get("pressure", "—")) }}</p>
    <p><strong>Exit Signal:</strong> {{ sell.get("exit_signal", sell.get("decision", "—")) }}</p>
    <p><strong>Reason:</strong> {{ sell.get("reason", sell.get("summary", "No exit warning yet.")) }}</p>
  </div>
</section>

<section class="grid">
  <div class="card">
    <h2>🎮 Daily Missions</h2>
    <p><strong>Mission 1:</strong> Only consider high-confidence setups.</p>
    <p><strong>Mission 2:</strong> Do not force trades in weak regimes.</p>
    <p><strong>Mission 3:</strong> Review missed opportunities before changing thresholds.</p>
  </div>

  <div class="card">
    <h2>🏆 Achievements</h2>
    <p><strong>System XP:</strong> {{ achievements.get("xp", "—") }}</p>
    <p><strong>Streak:</strong> {{ achievements.get("streak", "—") }}</p>
    <p><strong>Latest:</strong> {{ achievements.get("latest", "Keep collecting clean research data.") }}</p>
  </div>

  <div class="card">
    <h2>🧠 Learning Mode</h2>
    <p>Plain-English summaries, safe explanations, and daily upgrade suggestions belong here.</p>
    <p class="muted">Future: coding lessons, trading lessons, IPO watchlists, crypto/ETF/commodities research labs.</p>
  </div>

  <div class="card">
    <h2>♿ Accessibility / ADHD</h2>
    <p>Black professional theme, strong outlines, colorblind-friendly labels, larger click zones, and reduced motion.</p>
    <p class="muted">Future: focus mode, compact mode, big-card mode, and custom accent colors.</p>
  </div>
</section>

<section class="card">
  <h2>🧠 Plain-English AI Summary</h2>
  <ul class="summary-list">
    {% for item in ai.get("plain_english_summary", []) %}
      <li>{{ item }}</li>
    {% else %}
      <li>No plain-English summary yet.</li>
    {% endfor %}
  </ul>
</section>

<section class="grid">
  <a class="card module-link" href="/research">
    <h3>🧠 Research Center</h3>
    <p>AI summary, alerts, scanner, overnight, sell, rotation, performance, and raw JSON intelligence.</p>
  </a>

  <a class="card module-link" href="/assistant">
    <h3>🐕 Ask Ponder</h3>
    <p>Ponder assistant interface for explanations, risk warnings, and next-step guidance.</p>
  </a>

  <a class="card module-link" href="/learning">
    <h3>🎮 Learning Center</h3>
    <p>Achievements, daily missions, XP, trading education, and coding-friendly explanations.</p>
  </a>

  <a class="card module-link" href="/settings">
    <h3>⚙️ Settings</h3>
    <p>Future: theme, accessibility, notification cadence, security, and dashboard layout controls.</p>
  </a>
</section>

<section class="card roadmap">
  <h2>Expandable Build Roadmap</h2>
  <div class="roadmap-grid">
    <div><strong>1. Adaptive Capital Allocator</strong><p>Confidence-based sizing and risk mode.</p></div>
    <div><strong>2. Position Ranking View</strong><p>Best to worst current positions with replace logic.</p></div>
    <div><strong>3. Performance Learning UI</strong><p>What signals are actually working.</p></div>
    <div><strong>4. Shadow Execution</strong><p>Simulated buy/sell validation before automation.</p></div>
    <div><strong>5. Smart Notifications</strong><p>Periodic AI monitoring without spam.</p></div>
    <div><strong>6. Future Research Labs</strong><p>IPO, crypto, ETF, commodities, day trading, TikTok/news trend scanners.</p></div>
  </div>
</section>

<script>
async function refreshDashboard() {
  try {
    const res = await fetch("/api/dashboard", { cache: "no-store" });
    if (!res.ok) return;
    console.log("Ponder live data refreshed", await res.json());
  } catch (err) {
    console.log("Live refresh unavailable", err);
  }
}
setInterval(refreshDashboard, 30000);
</script>

{% endblock %}
'''

(SITE / "app.py").write_text(APP)
(TEMPLATES / "dashboard.html").write_text(DASHBOARD)

print("✅ Command Center v2 installed.")
print("Updated:")
print(" - new_ponder_site/app.py")
print(" - new_ponder_site/templates/dashboard.html")
print("")
print("Next:")
print("cd /home/ubuntu/trading-bot")
print("source venv/bin/activate")
print("python3 new_ponder_site/app.py")
