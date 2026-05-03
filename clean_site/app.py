from flask import Flask, render_template, jsonify, send_from_directory
from pathlib import Path
import json, os

app = Flask(__name__)

ROOT = Path("/home/ubuntu/trading-bot")
RESEARCH = ROOT / "static" / "research"

def read_json(name):
    p = RESEARCH / name
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception as e:
        return {"error": str(e), "file": name}

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/research")
def research():
    return render_template("research.html")

@app.route("/assistant")
def assistant():
    return render_template("assistant.html")

@app.route("/learning")
def learning():
    return render_template("learning.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/api/research/<name>")
def api_research(name):
    allowed = {
        "ai": "ai_summary_latest.json",
        "alerts": "notifications_latest.json",
        "market": "market_intelligence_latest.json",
        "overnight": "overnight_brief_latest.json",
        "sell": "sell_intelligence_latest.json",
        "rotation": "rotation_engine_latest.json",
        "performance": "rotation_performance_latest.json",
        "shadow": "shadow_capital_allocator_latest.json",
        "regime": "market_regime_filter_latest.json",
        "achievements": "achievements_latest.json",
        "assistant": "ponder_assistant_latest.json",
    }
    if name not in allowed:
        return jsonify({"error": "unknown research feed"}), 404
    return jsonify(read_json(allowed[name]))

@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory(ROOT / "clean_site" / "static", path)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050)
