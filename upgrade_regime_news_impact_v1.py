from pathlib import Path

p = Path("market_regime_filter_v1.py")
text = p.read_text()

old = '''    risk_score = float(overnight.get("risk_score", 50))
    index_moves = overnight.get("index_moves", [])
    sell_candidates = sell.get("sell_candidates", [])
    trade_ready = scanner.get("trade_ready", [])'''

new = '''    risk_score = float(overnight.get("risk_score", 50))
    news_impact = float(overnight.get("news_impact", 0) or 0)
    news_items = overnight.get("news", []) or []
    index_moves = overnight.get("index_moves", [])
    sell_candidates = sell.get("sell_candidates", [])
    trade_ready = scanner.get("trade_ready", [])'''

text = text.replace(old, new)

old = '''    if avg_sell > 50:
        score -= 8
        reasons.append("elevated sell pressure")'''

new = '''    if avg_sell > 50:
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
        reasons.append("positive high-impact news support detected")'''

text = text.replace(old, new)

old = '''        "regime_score": score,
        "reasons": reasons,
        "notes": ['''

new = '''        "regime_score": score,
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
        "notes": ['''

text = text.replace(old, new)

p.write_text(text)
print("✅ market_regime_filter_v1.py now uses overnight news impact")
