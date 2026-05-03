import json
from datetime import datetime
from pathlib import Path

OUT = Path("static/research")
OUT.mkdir(parents=True, exist_ok=True)

OVERNIGHT = OUT / "overnight_brief_latest.json"
SCANNER = OUT / "market_intelligence_latest.json"
SELL = OUT / "sell_intelligence_latest.json"
DEST = OUT / "market_regime_filter_latest.json"

def load_json(path):
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except:
        return {}

def clamp(n, low=0, high=100):
    return max(low, min(high, n))

def classify(overnight, scanner, sell):
    risk_score = float(overnight.get("risk_score", 50))
    news_impact = float(overnight.get("news_impact", 0) or 0)
    news_items = overnight.get("news", []) or []
    index_moves = overnight.get("index_moves", [])
    sell_candidates = sell.get("sell_candidates", [])
    trade_ready = scanner.get("trade_ready", [])

    avg_index = sum(x.get("change_1d_pct", 0) for x in index_moves) / len(index_moves) if index_moves else 0
    avg_sell = sum(x.get("sell_pressure", 0) for x in sell_candidates) / len(sell_candidates) if sell_candidates else 0

    score = 50
    reasons = []

    if risk_score >= 65:
        score += 15
        reasons.append("strong overnight risk score")
    elif risk_score <= 40:
        score -= 20
        reasons.append("weak overnight risk")

    if avg_index > 0.3:
        score += 10
        reasons.append("indices trending up")
    elif avg_index < -0.3:
        score -= 10
        reasons.append("indices trending down")

    if avg_sell > 50:
        score -= 8
        reasons.append("elevated sell pressure")

    risk_news = []
    positive_news = []

    for item in news_items:
        headline = str(item.get("headline", "")).lower()
        tags = [str(t).lower() for t in item.get("tags", [])]
        impact = float(item.get("impact_score", 0) or 0)

        if impact >= 60 and (
            "risk" in tags
            or "war" in headline
            or "tariff" in headline
            or "inflation" in headline
            or "rates" in headline
            or "fed" in headline
            or "oil" in headline
            or "china" in headline
            or "iran" in headline
        ):
            risk_news.append(item)

        if impact >= 60 and (
            "earnings" in tags
            or "ai/semis" in tags
            or "guidance" in headline
            or "beat" in headline
            or "growth" in headline
        ):
            positive_news.append(item)

    if news_impact >= 75 and risk_news:
        score -= 15
        reasons.append("high-impact risk news detected")
    elif news_impact >= 60 and risk_news:
        score -= 8
        reasons.append("moderate risk news detected")

    if news_impact >= 60 and positive_news and not risk_news:
        score += 5
        reasons.append("positive high-impact news support detected")

    if len(trade_ready) > 8:
        score += 5
        reasons.append("good opportunity flow")

    score = clamp(score)

    if score >= 68:
        regime = "Risk-On"
    elif score >= 55:
        regime = "Mild Risk-On"
    elif score >= 45:
        regime = "Neutral"
    else:
        regime = "Risk-Off"

    return score, regime, reasons

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    overnight = load_json(OVERNIGHT)
    scanner = load_json(SCANNER)
    sell = load_json(SELL)

    score, regime, reasons = classify(overnight, scanner, sell)

    payload = {
        "updated_at": now,
        "version": "v1",
        "status": "research_only",
        "regime": regime,
        "regime_score": score,
        "news_impact": overnight.get("news_impact", 0),
        "top_news": [
            {
                "headline": x.get("headline"),
                "source": x.get("source"),
                "impact_score": x.get("impact_score"),
                "tags": x.get("tags", [])
            }
            for x in (overnight.get("news", []) or [])[:5]
        ],
        "reasons": reasons,
        "notes": [
            "Used to adjust rotation aggressiveness later",
            "Does not affect trading yet"
        ]
    }

    DEST.write_text(json.dumps(payload, indent=2))
    print("Saved:", DEST)
    print(json.dumps(payload, indent=2))

if __name__ == "__main__":
    main()
