import json
from datetime import datetime
from pathlib import Path

OUT = Path("static/research")
DEST = OUT / "ponder_assistant_latest.json"

FILES = {
    "ai": OUT / "ai_summary_latest.json",
    "alerts": OUT / "notifications_latest.json",
    "regime": OUT / "market_regime_filter_latest.json",
    "rotation": OUT / "rotation_engine_latest.json",
    "performance": OUT / "rotation_performance_latest.json",
    "shadow": OUT / "shadow_capital_allocator_latest.json",
    "sell": OUT / "sell_intelligence_latest.json",
    "market": OUT / "market_intelligence_latest.json",
}

def load_json(path):
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:
        return {}

def safe(v, fallback="unknown"):
    return fallback if v in [None, "", [], {}] else v

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    d = {k: load_json(v) for k, v in FILES.items()}

    regime = d["regime"]
    rotation = d["rotation"]
    perf = d["performance"]
    alerts = d["alerts"]
    ai = d["ai"]
    sell = d["sell"]
    market = d["market"]

    top_rotation = rotation.get("top_rotation", {}) or {}
    top_exit = sell.get("top_exit_candidate", {}) or {}
    perf_summary = perf.get("summary", {}) or {}
    alert_summary = alerts.get("summary", {}) or {}
    trade_ready = market.get("trade_ready", []) or []

    regime_name = safe(regime.get("regime"))
    news_impact = float(regime.get("news_impact", 0) or 0)

    answers = {
        "why_no_trade": [],
        "biggest_risk": [],
        "should_rotate": [],
        "what_to_do": ai.get("action_items", []),
        "plain_english": ai.get("plain_english_summary", []),
    }

    if regime_name == "Risk-Off":
        answers["why_no_trade"].append("🐕 Ponder is guarding you right now. The market is Risk-Off.")
    if news_impact >= 70:
        answers["why_no_trade"].append(f"Big news risk is active at {news_impact}/100, so forcing trades is unsafe.")
    if top_rotation:
        answers["why_no_trade"].append(f"Top idea is {top_rotation.get('sell_symbol')} → {top_rotation.get('buy_symbol')}, but action is {top_rotation.get('action')} with {top_rotation.get('confidence')} confidence.")
    if perf_summary.get("evaluated", 0) == 0:
        answers["why_no_trade"].append("The learning tracker still needs evaluated outcomes before trusting rotation signals.")
    answers["why_no_trade"].append("Ponder says: better to wait than make a bad trade.")

    if news_impact >= 70:
        answers["biggest_risk"].append("High-impact news is the biggest risk.")
    if regime_name == "Risk-Off":
        answers["biggest_risk"].append("Market regime is defensive.")
    if alert_summary.get("critical", 0):
        answers["biggest_risk"].append(f"There are {alert_summary.get('critical')} critical alert(s).")
    if top_exit:
        answers["biggest_risk"].append(f"Sell intelligence is watching {top_exit.get('symbol')} with sell pressure {top_exit.get('sell_pressure')}/100.")

    if top_rotation:
        answers["should_rotate"].append(f"Current top rotation: {top_rotation.get('sell_symbol')} → {top_rotation.get('buy_symbol')}.")
        answers["should_rotate"].append(f"Action: {top_rotation.get('action')} | Confidence: {top_rotation.get('confidence')} | Score: {top_rotation.get('rotation_score')}.")
    answers["should_rotate"].append("Ponder does not recommend treating this as actionable unless it says ROTATE NOW with strong confidence.")
    answers["should_rotate"].append("Still research-only. No live trades.")

    opportunity = "No strong trade-ready names are currently available."
    if trade_ready:
        opportunity = "Trade-ready names being watched: " + ", ".join([x.get("symbol", "?") for x in trade_ready[:8]]) + "."

    payload = {
        "updated_at": now,
        "version": "ponder_assistant_v1_dog_theme",
        "status": "research_only",
        "assistant_name": "Ponder 🐕",
        "role": "Loyal AI watchdog — monitors markets, explains risks, and keeps you from forcing bad trades.",
        "personality": {
            "style": "loyal_black_lab_chow_mix_watchdog",
            "phrases": {
                "risk_off": "🐕 Ponder is being cautious — the market feels unsafe.",
                "risk_on": "🐕 Ponder sees opportunity, but is still watching closely.",
                "no_trade": "🐕 Ponder says: better to wait than make a bad trade."
            }
        },
        "overseer": {
            "system_mode": "research_only",
            "market_regime": regime_name,
            "news_impact": news_impact,
            "alert_count": alert_summary.get("total", 0),
            "critical_alerts": alert_summary.get("critical", 0),
            "top_rotation": {
                "move": f"{safe(top_rotation.get('sell_symbol'))} -> {safe(top_rotation.get('buy_symbol'))}",
                "action": top_rotation.get("action"),
                "confidence": top_rotation.get("confidence"),
                "score": top_rotation.get("rotation_score"),
            },
            "learning": {
                "evaluated": perf_summary.get("evaluated", 0),
                "pending": perf_summary.get("pending_evaluations", 0),
                "win_rate": perf_summary.get("win_rate", 0),
            },
            "opportunity": opportunity,
        },
        "answers": answers,
        "suggested_questions": [
            "Why didn’t you trade?",
            "What is the biggest risk right now?",
            "Should I rotate?",
            "What should I do right now?",
            "Explain this in simple terms."
        ],
        "notes": ["Research-only. No live trades. No AI API yet."]
    }

    DEST.write_text(json.dumps(payload, indent=2))
    print("Saved:", DEST)

if __name__ == "__main__":
    main()
