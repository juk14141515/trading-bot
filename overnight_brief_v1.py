import json
import os
from dotenv import load_dotenv
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

load_dotenv(dotenv_path=".env")

import pandas as pd
import yfinance as yf

OUT = Path("static/research")
OUT.mkdir(parents=True, exist_ok=True)

INDEXES = {
    "SPY": "S&P 500 ETF",
    "QQQ": "Nasdaq 100 ETF",
    "IWM": "Small Caps ETF",
    "DIA": "Dow ETF",
    "ES=F": "S&P Futures",
    "NQ=F": "Nasdaq Futures",
    "YM=F": "Dow Futures",
    "RTY=F": "Russell Futures",
}

WATCH = [
    "NVDA", "AMD", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA",
    "QCOM", "MU", "INTC", "AVGO", "SMCI", "COIN", "PLTR"
]


def flatten(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df.dropna()


def get_move(symbol, days=7):
    end = datetime.now()
    start = end - timedelta(days=days + 5)

    df = yf.download(
        symbol,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        interval="1d",
        progress=False,
        auto_adjust=True,
    )

    if df.empty or len(df) < 2:
        return None

    df = flatten(df)
    close = df["Close"].astype(float)
    volume = df["Volume"].astype(float)

    last = float(close.iloc[-1])
    prev = float(close.iloc[-2])
    change_1d = (last - prev) / prev * 100

    change_5d = 0
    if len(close) >= 6:
        change_5d = (last - float(close.iloc[-6])) / float(close.iloc[-6]) * 100

    avg_vol = float(volume.tail(10).mean()) if len(volume) >= 10 else float(volume.mean())
    vol_ratio = float(volume.iloc[-1] / avg_vol) if avg_vol else 1

    return {
        "symbol": symbol,
        "price": round(last, 2),
        "change_1d_pct": round(change_1d, 2),
        "change_5d_pct": round(change_5d, 2),
        "volume_ratio": round(vol_ratio, 2),
    }



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


def risk_label(index_moves):
    if not index_moves:
        return "Unknown", 50

    avg_1d = sum(x["change_1d_pct"] for x in index_moves) / len(index_moves)

    if avg_1d > 0.8:
        return "Risk-On / Bullish", 80
    if avg_1d > 0.2:
        return "Mild Risk-On", 65
    if avg_1d > -0.3:
        return "Neutral / Mixed", 50
    if avg_1d > -1.0:
        return "Caution / Weak Tape", 35
    return "Risk-Off / Defensive", 20


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    index_moves = []
    for symbol, name in INDEXES.items():
        data = get_move(symbol)
        if data:
            data["name"] = name
            index_moves.append(data)

    movers = []
    for symbol in WATCH:
        data = get_move(symbol)
        if data:
            movers.append(data)

    movers = sorted(movers, key=lambda x: x["change_1d_pct"], reverse=True)

    top_strength = movers[:5]
    top_weakness = sorted(movers, key=lambda x: x["change_1d_pct"])[:5]

    market_label, risk_score = risk_label(index_moves)
    news = get_finnhub_news()

    news_impact = max([x.get("impact_score", 0) for x in news], default=0)
    if news_impact >= 80:
        risk_score = max(10, risk_score - 10)
        market_label = market_label + " / News Sensitive"

    notes = []

    if top_strength:
        notes.append(
            "Strongest watchlist names: " +
            ", ".join([f"{x['symbol']} ({x['change_1d_pct']}%)" for x in top_strength[:3]])
        )

    if top_weakness:
        notes.append(
            "Weakest watchlist names: " +
            ", ".join([f"{x['symbol']} ({x['change_1d_pct']}%)" for x in top_weakness[:3]])
        )

    if news:
        notes.append("Top news: " + news[0].get("headline", "No headline"))

    if risk_score >= 65:
        notes.append("Market backdrop favors selective momentum / pullback entries.")
    elif risk_score <= 35:
        notes.append("Market backdrop suggests caution, smaller sizing, or fewer new entries.")
    else:
        notes.append("Market backdrop is mixed; prioritize quality setups and avoid chasing extended names.")

    payload = {
        "updated_at": now,
        "market_label": market_label,
        "risk_score": risk_score,
        "index_moves": index_moves,
        "top_strength": top_strength,
        "top_weakness": top_weakness,
        "notes": notes,
        "news": news,
        "news_impact": news_impact,
        "status": "research_only",
    }

    latest = OUT / "overnight_brief_latest.json"
    latest.write_text(json.dumps(payload, indent=2))

    archive = OUT / f"overnight_brief_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    archive.write_text(json.dumps(payload, indent=2))

    print("Saved:", latest)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
