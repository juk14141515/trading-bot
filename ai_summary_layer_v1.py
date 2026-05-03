import json
from datetime import datetime
from pathlib import Path

OUT = Path("static/research")
DEST = OUT / "ai_summary_latest.json"

FILES = {
    "overnight": OUT / "overnight_brief_latest.json",
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
    return fallback if v in [None, "", []] else v

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data = {k: load_json(v) for k, v in FILES.items()}

    overnight = data["overnight"]
    regime = data["regime"]
    rotation = data["rotation"]
    performance = data["performance"]
    shadow = data["shadow"]
    sell = data["sell"]
    market = data["market"]

    regime_name = safe(regime.get("regime"), overnight.get("market_label", "unknown"))
    regime_score = safe(regime.get("regime_score"), overnight.get("risk_score", "unknown"))
    news_impact = overnight.get("news_impact", 0)
    top_news = (overnight.get("news") or [])[:3]

    rot_summary = rotation.get("summary", {})
    top_rotation = rotation.get("top_rotation", {})
    perf_summary = performance.get("summary", {})
    shadow_summary = shadow.get("summary", {})
    top_shadow = shadow.get("top_shadow_action", {})
    top_exit = sell.get("top_exit_candidate", {})
    trade_ready = market.get("trade_ready", []) or []

    plain = []

    if regime_name == "Risk-Off":
        plain.append("Market conditions look defensive because high-impact news risk is active.")
    elif "Risk-On" in str(regime_name):
        plain.append("Market conditions are generally supportive, but individual setups still need confirmation.")
    else:
        plain.append("Market conditions are mixed, so the system should be selective.")

    if news_impact and news_impact >= 70:
        plain.append(f"News impact is elevated at {news_impact}/100, so the system should avoid forcing aggressive rotations.")
    elif news_impact:
        plain.append(f"News impact is moderate at {news_impact}/100.")
    else:
        plain.append("No major news impact is currently being detected.")

    if top_rotation:
        plain.append(
            f"Top rotation idea is {top_rotation.get('sell_symbol')} → {top_rotation.get('buy_symbol')}, "
            f"but action is {top_rotation.get('action')} with {top_rotation.get('confidence', 'unknown')} confidence."
        )
    else:
        plain.append("No strong rotation idea is available right now.")

    if top_shadow:
        plain.append(
            f"Shadow allocator is tracking {top_shadow.get('sell_symbol')} → {top_shadow.get('buy_symbol')} "
            f"as a simulated move only."
        )
    else:
        plain.append("Shadow allocator is not recommending any simulated move right now.")

    if perf_summary.get("evaluated", 0) == 0:
        plain.append("Performance tracker is still waiting for enough 30m/60m/120m outcomes before judging rotations.")
    else:
        plain.append(
            f"Rotation tracker has a {perf_summary.get('win_rate', 0)}% win rate at the primary "
            f"{perf_summary.get('primary_horizon', '60m')} window."
        )

    if top_exit:
        plain.append(
            f"Sell intelligence is watching {top_exit.get('symbol')} with sell pressure "
            f"{top_exit.get('sell_pressure')}/100."
        )

    if trade_ready:
        names = ", ".join([x.get("symbol", "?") for x in trade_ready[:5]])
        plain.append(f"Top trade-ready names include: {names}.")

    action_items = []

    if regime_name == "Risk-Off":
        action_items.append("Stay defensive. Avoid treating Watch Rotation as permission to trade.")
        action_items.append("Let the tracker collect outcomes during high-news-risk conditions.")
    else:
        action_items.append("Monitor top rotation ideas but keep them research-only.")
        action_items.append("Focus on trade-ready names that are not extended.")

    action_items.append("Do not connect this to live trading yet.")
    action_items.append("Check whether pending tracker evaluations start resolving after 30–60 minutes.")

    payload = {
        "updated_at": now,
        "version": "ai_summary_layer_v1",
        "status": "research_only",
        "plain_english_summary": plain,
        "action_items": action_items,
        "key_readout": {
            "regime": regime_name,
            "regime_score": regime_score,
            "news_impact": news_impact,
            "top_rotation": {
                "move": f"{safe(top_rotation.get('sell_symbol'))} -> {safe(top_rotation.get('buy_symbol'))}",
                "action": top_rotation.get("action"),
                "confidence": top_rotation.get("confidence"),
                "score": top_rotation.get("rotation_score"),
            },
            "shadow_moves": shadow_summary.get("shadow_moves"),
            "rotation_win_rate": perf_summary.get("win_rate"),
            "pending_evaluations": perf_summary.get("pending_evaluations"),
        },
        "top_news": [
            {
                "headline": n.get("headline"),
                "source": n.get("source"),
                "impact_score": n.get("impact_score"),
                "tags": n.get("tags", []),
            }
            for n in top_news
        ],
        "notes": [
            "AI Summary Layer v1 is research-only.",
            "It explains system state in simple language.",
            "It does not place trades or change bot behavior."
        ],
    }

    DEST.write_text(json.dumps(payload, indent=2))
    print("Saved:", DEST)
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
