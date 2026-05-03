
from flask import Flask, render_template
import json
import csv
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR if (APP_DIR / "static" / "research").exists() else APP_DIR.parent
RESEARCH = ROOT / "static" / "research"

app = Flask(
    __name__,
    template_folder=str((APP_DIR / "templates") if (APP_DIR / "templates").exists() else (ROOT / "templates")),
    static_folder=str((APP_DIR / "static") if (APP_DIR / "static").exists() else (ROOT / "static")),
)

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

def first_item(data, key):
    items = data.get(key) or []
    return items[0] if items else {}

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

@app.route("/api/dashboard-data")
def dashboard_data():
    bot = load_root_json("bot_status.json")
    ai = load_json("ai_summary_latest.json")
    alerts = load_json("notifications_latest.json")
    market = load_json("market_intelligence_latest.json")
    rotation = load_json("rotation_engine_latest.json")
    sell = load_json("sell_intelligence_latest.json")
    shadow = load_json("shadow_capital_allocator_latest.json")
    capital = load_json("capital_intelligence_latest.json")
    regime = load_json("market_regime_filter_latest.json")

    return {
        "bot": bot,
        "ai": ai,
        "alerts": alerts,
        "market": market,
        "regime": regime,
        "capital": capital,
        "capital_history": load_capital_history(),
        "scanner_top": (market.get("scanner_top") or [])[:8],
        "top_rotation": first_item(rotation, "rotation_suggestions"),
        "rotation_suggestions": (rotation.get("rotation_suggestions") or [])[:8],
        "top_exit": sell.get("top_exit_candidate") or first_item(sell, "sell_candidates"),
        "sell_candidates": (sell.get("sell_candidates") or [])[:8],
        "top_shadow": first_item(shadow, "shadow_actions"),
        "shadow_actions": (shadow.get("shadow_actions") or [])[:8],
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
