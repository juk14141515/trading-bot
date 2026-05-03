from pathlib import Path

p = Path("overnight_brief_v1.py")
text = p.read_text()
p.with_suffix(".py.bak_news_futures_v1").write_text(text)

text = text.replace(
'''INDEXES = {
    "SPY": "S&P 500 ETF",
    "QQQ": "Nasdaq 100 ETF",
    "IWM": "Small Caps ETF",
    "DIA": "Dow ETF",
}''',
'''INDEXES = {
    "SPY": "S&P 500 ETF",
    "QQQ": "Nasdaq 100 ETF",
    "IWM": "Small Caps ETF",
    "DIA": "Dow ETF",
    "ES=F": "S&P Futures",
    "NQ=F": "Nasdaq Futures",
    "YM=F": "Dow Futures",
    "RTY=F": "Russell Futures",
}'''
)

if "import os" not in text:
    text = text.replace("import json", "import json\nimport os\nimport urllib.request\nimport urllib.parse")

NEWS_FN = r'''

def get_finnhub_news():
    key = os.getenv("FINNHUB_API_KEY")
    if not key:
        return []

    try:
        today = datetime.now().date()
        start = today - timedelta(days=2)

        url = (
            "https://finnhub.io/api/v1/news?"
            + urllib.parse.urlencode({
                "category": "general",
                "token": key
            })
        )

        with urllib.request.urlopen(url, timeout=12) as r:
            raw = json.loads(r.read().decode("utf-8"))

        items = []
        for x in raw[:12]:
            headline = x.get("headline") or ""
            summary = x.get("summary") or ""
            source = x.get("source") or "news"
            related = x.get("related") or ""
            ts = x.get("datetime")

            if not headline:
                continue

            text_blob = (headline + " " + summary + " " + related).lower()

            impact = 50
            tags = []

            if any(w in text_blob for w in ["fed", "rate", "inflation", "cpi", "pce", "jobs", "payroll"]):
                impact += 20
                tags.append("macro")

            if any(w in text_blob for w in ["nvidia", "ai", "chip", "semiconductor", "amd", "intel"]):
                impact += 15
                tags.append("ai/semis")

            if any(w in text_blob for w in ["war", "oil", "tariff", "china", "geopolitical"]):
                impact += 15
                tags.append("risk")

            if any(w in text_blob for w in ["earnings", "guidance", "revenue", "profit"]):
                impact += 10
                tags.append("earnings")

            impact = min(100, impact)

            items.append({
                "headline": headline,
                "source": source,
                "impact_score": impact,
                "tags": tags,
                "url": x.get("url", ""),
                "datetime": ts,
            })

        return sorted(items, key=lambda x: x["impact_score"], reverse=True)[:8]
    except Exception as e:
        return [{"headline": f"News unavailable: {e}", "source": "system", "impact_score": 0, "tags": ["error"]}]
'''

if "def get_finnhub_news()" not in text:
    text = text.replace("\ndef risk_label(index_moves):", NEWS_FN + "\n\ndef risk_label(index_moves):")

text = text.replace(
'''    market_label, risk_score = risk_label(index_moves)

    notes = []''',
'''    market_label, risk_score = risk_label(index_moves)
    news = get_finnhub_news()

    news_impact = max([x.get("impact_score", 0) for x in news], default=0)
    if news_impact >= 80:
        risk_score = max(10, risk_score - 10)
        market_label = market_label + " / News Sensitive"

    notes = []'''
)

text = text.replace(
'''    if risk_score >= 65:
        notes.append("Market backdrop favors selective momentum / pullback entries.")''',
'''    if news:
        notes.append("Top news: " + news[0].get("headline", "No headline"))

    if risk_score >= 65:
        notes.append("Market backdrop favors selective momentum / pullback entries.")'''
)

text = text.replace(
'''        "notes": notes,
        "status": "research_only",''',
'''        "notes": notes,
        "news": news,
        "news_impact": news_impact,
        "status": "research_only",'''
)

p.write_text(text)
print("✅ Overnight upgraded with futures + Finnhub news")
