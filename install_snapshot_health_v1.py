from pathlib import Path

ROOT = Path(".")
SNAP = ROOT / "system_snapshot.py"
PIPE = ROOT / "research_pipeline_v1.py"

SNAP.write_text(r'''import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESEARCH = ROOT / "static" / "research"
OUT = RESEARCH / "system_snapshot_latest.json"

FILES = {
    "capital": "capital_intelligence_latest.json",
    "decisions": "decision_engine_latest.json",
    "ai": "ai_summary_latest.json",
    "alerts": "notifications_latest.json",
    "market": "market_intelligence_latest.json",
    "overnight": "overnight_brief_latest.json",
    "sell": "sell_intelligence_latest.json",
    "rotation": "rotation_engine_latest.json",
    "performance": "rotation_performance_latest.json",
    "shadow": "shadow_capital_allocator_latest.json",
    "regime": "market_regime_filter_latest.json",
}

def load_json(name):
    path = RESEARCH / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}

def status(data):
    return "online" if bool(data) else "missing"

def main():
    data = {key: load_json(file) for key, file in FILES.items()}

    capital = data["capital"]
    decisions = data["decisions"]
    ai = data["ai"]
    alerts = data["alerts"]
    rotation = data["rotation"]
    sell = data["sell"]

    decision_summary = decisions.get("summary", {})
    decision_list = decisions.get("decisions", [])
    top = decision_list[0] if decision_list else {}

    modules = {
        "capital_engine": status(capital),
        "decision_engine": status(decisions),
        "ai_summary": status(ai),
        "alerts": status(alerts),
        "market_intelligence": status(data["market"]),
        "overnight_intelligence": status(data["overnight"]),
        "sell_intelligence": status(sell),
        "rotation_engine": status(rotation),
        "performance_tracker": status(data["performance"]),
        "shadow_allocator": status(data["shadow"]),
        "market_regime": status(data["regime"]),
    }

    online_count = sum(1 for v in modules.values() if v == "online")
    health_score = round((online_count / max(len(modules), 1)) * 100)

    snapshot = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "research_only",
        "health_score": health_score,
        "modules": modules,
        "capital": {
            "portfolio": capital.get("equity", 0),
            "cash": capital.get("cash", 0),
            "buying_power": capital.get("buying_power", 0),
            "deployable": capital.get("deployable_cash", 0),
            "capital_mode": capital.get("capital_mode", "UNKNOWN"),
            "capital_efficiency": capital.get("capital_efficiency", "UNKNOWN"),
            "next_money_action": capital.get("next_money_action", "No capital guidance yet."),
        },
        "decision": {
            "buy_count": decision_summary.get("buy_count", 0),
            "watch_count": decision_summary.get("watch_count", 0),
            "ignore_count": decision_summary.get("ignore_count", 0),
            "top_symbol": top.get("symbol", "—"),
            "top_score": top.get("score", "—"),
            "top_action": top.get("action", "—"),
            "top_reason": top.get("reason", "—"),
        },
        "risk": {
            "alerts_total": alerts.get("summary", {}).get("total", 0),
            "critical": alerts.get("summary", {}).get("critical", 0),
            "warning": alerts.get("summary", {}).get("warning", 0),
            "sell_pressure_top": sell.get("sell_candidates", [{}])[0].get("sell_pressure", "—") if sell.get("sell_candidates") else "—",
        },
        "plain_english": [
            f"System health is {health_score}/100.",
            f"Capital mode is {capital.get('capital_mode', 'UNKNOWN')}.",
            f"Top setup is {top.get('symbol', '—')} with action {top.get('action', '—')}.",
            capital.get("next_money_action", "No capital guidance yet."),
            "Everything is research-only. No live orders are placed."
        ],
    }

    OUT.write_text(json.dumps(snapshot, indent=2))
    print("Saved:", OUT)
    print(json.dumps({"health_score": health_score, "top_symbol": snapshot["decision"]["top_symbol"]}, indent=2))

if __name__ == "__main__":
    main()
''')

if PIPE.exists():
    original = PIPE.read_text()
    PIPE.with_suffix(".py.backup_snapshot_health_v1").write_text(original)
    if 'run(["python3", "system_snapshot.py"])' not in original:
        if 'run(["python3", "capital_intelligence_v1.py"])' in original:
            updated = original.replace(
                'run(["python3", "capital_intelligence_v1.py"])',
                'run(["python3", "capital_intelligence_v1.py"])\n    run(["python3", "system_snapshot.py"])'
            )
        else:
            updated = original + '\n\n# Snapshot health update\nrun(["python3", "system_snapshot.py"])\n'
        PIPE.write_text(updated)

print("✅ Created system_snapshot.py")
print("✅ Patched research_pipeline_v1.py if available")
