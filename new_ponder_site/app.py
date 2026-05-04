
from flask import Flask, render_template, redirect, jsonify, request, session
import json
import csv
import sys
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

app = Flask(__name__)
ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "static" / "research"
load_dotenv(ROOT / ".env")
app.secret_key = os.getenv("PONDER_SECRET_KEY") or os.getenv("SECRET_KEY") or secrets.token_hex(32)
DASHBOARD_USERNAME = os.getenv("PONDER_DASHBOARD_USERNAME") or os.getenv("DASHBOARD_USERNAME") or "admin"
DASHBOARD_PASSWORD = os.getenv("PONDER_DASHBOARD_PASSWORD") or os.getenv("DASHBOARD_PASSWORD") or "change-me-now"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from profit_ops_analytics import snapshot as profit_ops_snapshot
except Exception as e:
    print(f"Profit Ops analytics unavailable: {e}")
    profit_ops_snapshot = None

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

def compact(value, default="unknown"):
    if value in (None, "", [], {}):
        return default
    return value

def as_float(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None

def money_display(value):
    number = as_float(value)
    if number is None:
        return "-"
    return f"${number:,.2f}"

def percent_display(value):
    number = as_float(value)
    if number is None:
        return "-"
    if abs(number) <= 1:
        number *= 100
    return f"{number:.2f}%"

def normalize_position(raw):
    if not isinstance(raw, dict):
        return {}
    unrealized_pl = raw.get("unrealized_pl", raw.get("open_pl", raw.get("pnl")))
    pl_number = as_float(unrealized_pl)
    if pl_number is None:
        status = "watch"
    elif pl_number > 0:
        status = "profit"
    elif pl_number < 0:
        status = "loss"
    else:
        status = "watch"

    qty = raw.get("qty", raw.get("quantity", raw.get("shares")))
    qty_number = as_float(qty)
    return {
        "symbol": raw.get("symbol", raw.get("ticker", raw.get("asset", "-"))),
        "qty_display": f"{qty_number:g}" if qty_number is not None else compact(qty, "-"),
        "avg_entry_price_display": money_display(raw.get("avg_entry_price", raw.get("average_entry_price", raw.get("entry_price", raw.get("avg_price"))))),
        "current_price_display": money_display(raw.get("current_price", raw.get("last_price", raw.get("price")))),
        "market_value_display": money_display(raw.get("market_value", raw.get("value"))),
        "unrealized_pl_display": money_display(unrealized_pl),
        "unrealized_plpc_display": percent_display(raw.get("unrealized_plpc", raw.get("unrealized_pl_pct", raw.get("pnl_pct", raw.get("pl_pct"))))),
        "age_display": compact(raw.get("position_age", raw.get("age", raw.get("opened_at"))), "-"),
        "status": status,
        "status_label": {"profit": "Profit", "loss": "Loss", "watch": "Watch"}.get(status, "Watch"),
    }

def build_positions_snapshot(feeds):
    candidate_keys = (
        "positions",
        "open_positions",
        "current_positions",
        "holdings",
        "portfolio_positions",
    )
    for source, data in feeds.items():
        if not isinstance(data, dict):
            continue
        for key in candidate_keys:
            raw_positions = data.get(key)
            if raw_positions is None:
                continue
            if isinstance(raw_positions, dict):
                raw_positions = list(raw_positions.values())
            if not isinstance(raw_positions, list):
                continue
            positions = [p for p in (normalize_position(item) for item in raw_positions) if p]
            return {
                "available": True,
                "source": source,
                "updated_at": data.get("updated_at") or data.get("generated_at") or data.get("timestamp") or "unknown",
                "count": len(positions),
                "positions": positions,
                "warning": "",
            }
    bot_positions_count = as_float((feeds.get("bot_status") or {}).get("positions") if isinstance(feeds.get("bot_status"), dict) else None)
    if bot_positions_count is not None:
        return {
            "available": False,
            "source": "bot_status",
            "updated_at": (feeds.get("bot_status") or {}).get("status_updated_at", "unknown"),
            "count": int(bot_positions_count),
            "positions": [],
            "warning": "bot_status.json exposes only the open position count, not detailed holdings.",
        }
    return {
        "available": False,
        "source": "",
        "updated_at": "unknown",
        "count": 0,
        "positions": [],
        "warning": "Current positions data not exposed to dashboard yet.",
    }

def parse_timestamp(value):
    if not value:
        return None
    try:
        clean = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(clean)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None

def build_data_quality(feeds):
    rows = []
    now = datetime.now(timezone.utc)
    for name, data in feeds.items():
        updated = ""
        status = "missing"
        warning = "Missing feed"
        if isinstance(data, dict) and data:
            updated = data.get("updated_at") or data.get("generated_at") or data.get("status_updated_at") or data.get("timestamp") or ""
            parsed = parse_timestamp(updated)
            status = "present"
            warning = "Present"
            if parsed:
                age_minutes = int((now - parsed.astimezone(timezone.utc)).total_seconds() / 60)
                if age_minutes > 60:
                    status = "stale"
                    warning = f"Stale: {age_minutes} minutes old"
                else:
                    warning = f"Fresh: {age_minutes} minutes old"
            elif not updated:
                status = "warning"
                warning = "Present, timestamp missing"
        rows.append({
            "name": name,
            "status": status,
            "updated_at": updated or "unknown",
            "warning": warning,
        })
    return rows

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
    ai = load_json("ai_summary_latest.json")
    alerts = load_json("notifications_latest.json")
    performance = load_json("rotation_performance_latest.json")
    strategy_backtest = load_json("current_strategy_backtest_latest.json")
    forward_simulations = load_json("forward_setup_simulations_latest.json")
    bot = load_root_json("bot_status.json")
    profit_ops = build_profit_ops_data()
    positions = build_positions_snapshot({
        "market": market,
        "capital": capital,
        "profit_ops": profit_ops,
        "sell": sell,
        "shadow": shadow,
        "bot_status": bot,
    })
    data_feeds = {
        "bot_status": bot,
        "market": market,
        "capital": capital,
        "profit_ops": profit_ops,
        "alerts": alerts,
        "rotation": rotation,
        "sell": sell,
        "shadow": shadow,
        "performance": performance,
        "strategy_backtest": strategy_backtest,
        "forward_simulations": forward_simulations,
        "positions": positions if positions.get("available") else {},
    }
    return {
        "bot": bot,
        "ai": ai,
        "alerts": alerts,
        "market": market,
        "capital": capital,
        "profit_ops": profit_ops,
        "positions": positions,
        "capital_history": load_capital_history(),
        "strategy_backtest": strategy_backtest,
        "forward_simulations": forward_simulations,
        "scanner_top": (market.get("scanner_top") or [])[:6],
        "top_rotation": (rotation.get("rotation_suggestions") or [{}])[0],
        "top_exit": sell.get("top_exit_candidate") or (sell.get("sell_candidates") or [{}])[0],
        "top_shadow": (shadow.get("shadow_actions") or [{}])[0],
        "data_quality": build_data_quality(data_feeds),
        "module_health": build_module_health(data_feeds),
    }

def build_profit_ops_data():
    if not profit_ops_snapshot:
        return {
            "generated_at": "",
            "latest": {},
            "equity": [],
            "metrics": {},
            "drawdown": 0,
            "health": {"score": 0, "note": "Profit analytics module is unavailable."},
            "recent_trades": [],
            "recent_logs": [],
            "logs": {"counts": {}, "decision_feed": [], "warnings": []},
        }
    try:
        return profit_ops_snapshot()
    except Exception as e:
        return {
            "generated_at": "",
            "latest": {},
            "equity": [],
            "metrics": {},
            "drawdown": 0,
            "health": {"score": 0, "note": f"Profit analytics error: {e}"},
            "recent_trades": [],
            "recent_logs": [],
            "logs": {"counts": {}, "decision_feed": [], "warnings": [str(e)]},
        }

def build_module_health(feeds):
    health = []
    for name, data in feeds.items():
        updated = data.get("updated_at") or data.get("status_updated_at") or data.get("timestamp")
        status = "online" if data else "missing"
        if data and data.get("error"):
            status = "error"
        health.append({
            "name": name,
            "status": status,
            "updated_at": compact(updated, "not reported"),
            "items": len(data) if isinstance(data, dict) else 0,
        })
    return health

def build_feature_roadmap():
    return {
        "now": [
            {"name": "Dashboard consistency", "status": "active", "detail": "Keep every page on the same modular shell."},
            {"name": "Secure access", "status": "active", "detail": "Login guard, logout, security headers, and tunnel-first access."},
            {"name": "Snapshot handoff", "status": "active", "detail": "One-click context for Codex, ChatGPT, or cloud tasks."},
            {"name": "Learning mode visibility", "status": "active", "detail": "Show why the bot is waiting and what data is still missing."},
        ],
        "next": [
            {"name": "Adaptive Capital Allocator v1", "status": "next", "detail": "Recommend sizing from confidence, utilization, and recent performance."},
            {"name": "Unused Capital Optimizer", "status": "next", "detail": "Explain whether buying power should be deployed or protected."},
            {"name": "Sell Intelligence v2", "status": "next", "detail": "Compare hold vs sell expected value and simulated trailing stops."},
            {"name": "Shadow Execution Tracker", "status": "next", "detail": "Track would-have-sold and would-have-bought outcomes before automation."},
        ],
        "later": [
            {"name": "Overnight / Premarket Edge", "status": "planned", "detail": "Gap movers, earnings, sector rotation, futures/news risk."},
            {"name": "IPO Research Lab", "status": "planned", "detail": "Track IPO calendars, early behavior, lockups, and hype separately."},
            {"name": "Day Trading Lab", "status": "planned", "detail": "Fast scanner with different entries/exits, disconnected from live trading."},
            {"name": "Crypto / ETF / Commodities Labs", "status": "planned", "detail": "Separate research feeds with separate risk rules."},
            {"name": "Social Trend Scanner", "status": "planned", "detail": "Research TikTok/social catalysts without connecting to execution."},
            {"name": "Event Impact Layer", "status": "wait", "detail": "High power module. Wait until the base system is stable."},
        ],
        "guardrails": [
            "Keep new modules research-only until enough outcomes are logged.",
            "Do not connect auto-rotation until shadow win rate and edge are proven.",
            "Paper-test threshold changes before live use.",
            "Prefer clear explanations over more signals when learning.",
        ],
    }

def build_codex_cloud_handoff():
    return {
        "title": "Ponder Invest AI dashboard continuation",
        "task_prompt": (
            "You are continuing work on Ponder Invest AI, a personal research-only trading bot dashboard. "
            "Keep the new Flask app in new_ponder_site modular and consistent. Do not change live trading logic unless explicitly requested. "
            "Prioritize secure access, reusable templates, readable research cards, module health, snapshot handoff, larger graphs, "
            "Ponder branding, colorblind accessibility, and future research-only modules."
        ),
        "repo_expectation": "For Codex Cloud, push this project to a private GitHub repository, connect GitHub to ChatGPT/Codex, then start a cloud task with this prompt plus the Snapshot JSON.",
        "safe_files_first": [
            "new_ponder_site/app.py",
            "new_ponder_site/templates/",
            "new_ponder_site/static/style.css",
            "new_ponder_site/static/site/js/app.js",
        ],
        "avoid_without_review": [
            "bot.py live order logic",
            ".env secrets",
            "Alpaca API keys",
            "automatic sell/buy execution",
        ],
    }

def build_snapshot():
    data = build_dashboard_data()
    return {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "bot": data.get("bot"),
        "capital": data.get("capital"),
        "top_scanner": (data.get("scanner_top") or [{}])[0],
        "top_rotation": data.get("top_rotation"),
        "top_exit": data.get("top_exit"),
        "top_shadow": data.get("top_shadow"),
        "module_health": data.get("module_health"),
        "strategy_backtest": data.get("strategy_backtest"),
        "forward_simulations": data.get("forward_simulations"),
        "roadmap": build_feature_roadmap(),
        "codex_cloud_handoff": build_codex_cloud_handoff(),
        "next_build_targets": [
            "secure login and consistent UI",
            "card-based research views",
            "larger live equity/capital graphs",
            "module health and copy snapshot",
            "adaptive capital allocator v1",
            "unused capital optimizer",
            "overnight/premarket edge research",
            "IPO/day-trade/crypto research labs later, disconnected from live trading",
        ],
    }

@app.before_request
def require_login():
    allowed = (
        request.endpoint in {"login", "static"}
        or request.path.startswith("/static/")
        or request.path == "/health"
    )
    if allowed:
        return None
    if not session.get("authenticated"):
        return redirect("/login")
    return None

@app.after_request
def add_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        username_ok = secrets.compare_digest(username, DASHBOARD_USERNAME)
        password_ok = secrets.compare_digest(password, DASHBOARD_PASSWORD)
        if username_ok and password_ok:
            session.clear()
            session["authenticated"] = True
            session["username"] = username
            return redirect(request.args.get("next") or "/")
        error = "Invalid username or password."
    return render_template("login.html", error=error)

@app.route("/")
def dashboard():
    ai = load_json("ai_summary_latest.json")
    alerts = load_json("notifications_latest.json")
    dashboard_data = build_dashboard_data()
    return render_template("dashboard.html", ai=ai, alerts=alerts, dashboard_data=dashboard_data)

@app.route("/profit")
def profit_ops():
    dashboard_data = build_dashboard_data()
    return render_template("profit.html", dashboard_data=dashboard_data, profit=dashboard_data.get("profit_ops", {}))

@app.route("/profit-lab")
def profit_lab():
    dashboard_data = build_dashboard_data()
    return render_template("profit_lab.html", dashboard_data=dashboard_data, profit=dashboard_data.get("profit_ops", {}))

@app.route("/profit/history")
@app.route("/history")
def history():
    dashboard_data = build_dashboard_data()
    return render_template("history.html", dashboard_data=dashboard_data, profit=dashboard_data.get("profit_ops", {}))

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
        "capital": load_json("capital_intelligence_latest.json"),
        "shadow": load_json("shadow_capital_allocator_latest.json"),
        "regime": load_json("market_regime_filter_latest.json"),
        "strategy_backtest": load_json("current_strategy_backtest_latest.json"),
        "forward_simulations": load_json("forward_setup_simulations_latest.json"),
        "setup_performance": load_json("setup_performance_latest.json"),
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

@app.route("/build-plan")
def build_plan():
    return render_template("build_plan.html", roadmap=build_feature_roadmap(), handoff=build_codex_cloud_handoff())

@app.route("/settings")
def settings():
    return render_template("settings.html", module_health=build_dashboard_data().get("module_health", []))

@app.route("/health")
def health():
    return {"status": "ok", "site": "new_ponder_site"}

@app.route("/api/dashboard-data")
@app.route("/api/dashboard")
def api_dashboard_data():
    return jsonify(build_dashboard_data())

@app.route("/api/profit-ops")
def api_profit_ops():
    return jsonify(build_profit_ops_data())

@app.route("/api/snapshot")
def api_snapshot():
    return jsonify(build_snapshot())

@app.route("/debug-snapshot")
def debug_snapshot():
    return render_template("debug_snapshot.html", snapshot=build_snapshot())

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
