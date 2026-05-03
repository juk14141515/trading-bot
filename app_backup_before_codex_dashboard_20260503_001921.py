
from flask import Flask, render_template
import json
from pathlib import Path

app = Flask(__name__)
ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "static" / "research"

def load_json(name):
    p = RESEARCH / name
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}

@app.route("/")
def dashboard():
    ai = load_json("ai_summary_latest.json")
    alerts = load_json("notifications_latest.json")
    return render_template("dashboard.html", ai=ai, alerts=alerts)

@app.route("/research")
def research():
    data = {
        "ai": load_json("ai_summary_latest.json"),
        "alerts": load_json("notifications_latest.json"),
        "market": load_json("market_intelligence_latest.json"),
        "overnight": load_json("overnight_brief_latest.json"),
        "sell": load_json("sell_intelligence_latest.json"),
        "rotation": load_json("rotation_engine_latest.json"),
        "performance": load_json("rotation_performance_latest.json"),
        "shadow": load_json("shadow_capital_allocator_latest.json"),
        "regime": load_json("market_regime_filter_latest.json"),
    }
    return render_template("research.html", data=data)

@app.route("/assistant")
def assistant():
    ai = load_json("ai_summary_latest.json")
    assistant = load_json("ponder_assistant_latest.json")
    return render_template("assistant.html", ai=ai, assistant=assistant)

@app.route("/learning")
def learning():
    achievements = load_json("achievements_latest.json")
    performance = load_json("rotation_performance_latest.json")
    return render_template("learning.html", achievements=achievements, performance=performance)

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/health")
def health():
    return {"status": "ok", "site": "new_ponder_site"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
