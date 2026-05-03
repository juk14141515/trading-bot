import json
from pathlib import Path
from datetime import datetime

OUT = Path("static/research")
OUT.mkdir(parents=True, exist_ok=True)

def load(name):
    p = OUT / name
    if not p.exists():
        return {}
    return json.loads(p.read_text())

def main():
    regime = load("market_regime_filter_latest.json")
    rotation = load("rotation_engine_latest.json")
    ai = load("ai_summary_latest.json")

    alerts = []

    # 🚨 Regime alert
    if regime.get("regime_score", 50) <= 40:
        alerts.append({
            "level": "critical",
            "category": "regime",
            "title": "Risk-Off Market",
            "message": f"Market is defensive (score {regime.get('regime_score')})"
        })

    # ⚠️ News alert
    if regime.get("news_impact", 0) >= 70:
        alerts.append({
            "level": "warning",
            "category": "news",
            "title": "High News Impact",
            "message": f"News impact elevated at {regime.get('news_impact')}/100"
        })

    # 🧠 Rotation alert
    suggestions = rotation.get("rotation_suggestions", [])
    if suggestions:
        top = suggestions[0]
        if top.get("rotation_score", 0) >= 70:
            alerts.append({
                "level": "info",
                "category": "rotation",
                "title": "Strong Rotation Detected",
                "message": f"{top.get('sell_symbol')} → {top.get('buy_symbol')} ({top.get('rotation_score')})"
            })

    summary = {
        "critical": sum(1 for a in alerts if a["level"] == "critical"),
        "warning": sum(1 for a in alerts if a["level"] == "warning"),
        "achievement": sum(1 for a in alerts if a["level"] == "achievement"),
        "total": len(alerts)
    }

    out = {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "v1",
        "status": "research_only",
        "alerts": alerts,
        "summary": summary
    }

    (OUT / "notifications_latest.json").write_text(json.dumps(out, indent=2))
    print("🔔 Notifications updated")

if __name__ == "__main__":
    main()
