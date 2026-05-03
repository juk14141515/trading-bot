
from flask import Flask, render_template, redirect, jsonify
import json
import csv
import sys
from pathlib import Path

app = Flask(__name__)
ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "static" / "research"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def load_json(name):
    p = Path(name)
    if not p.is_absolute():
        p = RESEARCH / name
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}

def load_root_json(name):
    return load_json(ROOT / name)

def load_capital_history():
    capital = load_json("capital_intelligence_latest.json")
    history = capital.get("history") or []
    if history:
        return history[-120:]

    p = RESEARCH / "capital_history.csv"
    if not p.exists():
        return []
    try:
        with p.open(newline="") as f:
            return list(csv.DictReader(f))[-120:]
    except Exception:
        return []

def build_dashboard_data():
    market = load_json("market_intelligence_latest.json")
    rotation = load_json("rotation_engine_latest.json")
    sell = load_json("sell_intelligence_latest.json")
    shadow = load_json("shadow_capital_allocator_latest.json")
    capital = load_json("capital_intelligence_latest.json")
    return {
        "bot": load_root_json("bot_status.json"),
        "ai": load_json("ai_summary_latest.json"),
        "alerts": load_json("notifications_latest.json"),
        "market": market,
        "capital": capital,
        "capital_history": load_capital_history(),
        "scanner_top": (market.get("scanner_top") or [])[:6],
        "top_rotation": (rotation.get("rotation_suggestions") or [{}])[0],
        "top_exit": sell.get("top_exit_candidate") or (sell.get("sell_candidates") or [{}])[0],
        "top_shadow": (shadow.get("shadow_actions") or [{}])[0],
    }

try:
    from profit_ops_routes import bp as profit_ops_bp
    app.register_blueprint(profit_ops_bp)
except Exception as e:
    print(f"Profit Ops routes unavailable: {e}")

try:
    from profit_lab_routes import profit_lab_bp
    app.register_blueprint(profit_lab_bp)
except Exception as e:
    print(f"Profit Lab routes unavailable: {e}")

@app.route("/")
def dashboard():
    ai = load_json("ai_summary_latest.json")
    alerts = load_json("notifications_latest.json")
    dashboard_data = build_dashboard_data()
    return render_template("dashboard.html", ai=ai, alerts=alerts, dashboard_data=dashboard_data)

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

@app.route("/api/dashboard-data")
@app.route("/api/dashboard")
def api_dashboard_data():
    return jsonify(build_dashboard_data())

@app.route("/history")
def history():
    return redirect("/profit/history")

@app.route("/logout")
def logout():
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
