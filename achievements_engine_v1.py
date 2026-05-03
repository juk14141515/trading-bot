import json
from pathlib import Path
from datetime import datetime

OUT = Path("static/research")
DEST = OUT / "achievements_latest.json"

def load(path):
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except:
        return {}

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    perf = load(OUT / "rotation_performance_latest.json")
    alerts = load(OUT / "notifications_latest.json")
    regime = load(OUT / "market_regime_filter_latest.json")

    summary = perf.get("summary", {})
    alert_summary = alerts.get("summary", {})

    achievements = []

    def unlock(id, title, desc):
        achievements.append({
            "id": id,
            "title": title,
            "description": desc,
            "unlocked": True
        })

    # 🎯 Learning milestones
    evaluated = summary.get("evaluated", 0)

    if evaluated >= 1:
        unlock("first_data", "🐾 First Steps", "Ponder started learning from real signals")

    if evaluated >= 10:
        unlock("data_10", "📊 Getting Smarter", "10 signals evaluated")

    if evaluated >= 50:
        unlock("data_50", "🧠 Pattern Hunter", "50 signals analyzed")

    # 🛡️ Risk awareness
    if regime.get("regime") == "Risk-Off":
        unlock("risk_guard", "🛡️ Guard Mode", "Detected defensive market conditions")

    if regime.get("news_impact", 0) >= 70:
        unlock("news_alert", "🚨 News Sniffer", "Detected high-impact news")

    # 🔔 Alerts awareness
    if alert_summary.get("critical", 0) > 0:
        unlock("critical_seen", "⚠️ Danger Sense", "Critical alert detected")

    total = len(achievements)

    payload = {
        "updated_at": now,
        "version": "v1",
        "status": "research_only",
        "total_unlocked": total,
        "achievements": achievements
    }

    DEST.write_text(json.dumps(payload, indent=2))
    print("Saved:", DEST)
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
