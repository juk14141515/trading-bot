import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

OUT = Path("static/research")
OUT.mkdir(parents=True, exist_ok=True)

WATCH = ["AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "GOOGL", "AMZN"]

DAYS_BACK = 15
INTERVAL = "5m"


def flatten(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df.dropna()


def analyze_symbol(symbol):
    end = datetime.now()
    start = end - timedelta(days=DAYS_BACK)

    df = yf.download(
        symbol,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        interval=INTERVAL,
        progress=False,
        auto_adjust=True,
    )

    if df.empty or len(df) < 50:
        return None

    df = flatten(df)
    close = df["Close"].astype(float)
    volume = df["Volume"].astype(float)

    price = float(close.iloc[-1])
    sma5 = float(close.tail(5).mean())
    sma20 = float(close.tail(20).mean())

    change_30m = float((close.iloc[-1] - close.iloc[-6]) / close.iloc[-6] * 100) if len(close) >= 6 else 0
    change_60m = float((close.iloc[-1] - close.iloc[-12]) / close.iloc[-12] * 100) if len(close) >= 12 else 0

    recent_high = float(close.tail(24).max())
    pullback_from_high = float((price - recent_high) / recent_high * 100)

    avg_vol = float(volume.tail(30).mean())
    vol_ratio = float(volume.iloc[-1] / avg_vol) if avg_vol else 1

    sell_pressure = 0
    reasons = []

    if price < sma5:
        sell_pressure += 15
        reasons.append("price below short SMA")

    if price < sma20:
        sell_pressure += 25
        reasons.append("price below 20-bar trend")

    if change_30m < -1:
        sell_pressure += 15
        reasons.append("weak 30m momentum")

    if change_60m < -2:
        sell_pressure += 20
        reasons.append("weak 60m momentum")

    if pullback_from_high < -2:
        sell_pressure += 20
        reasons.append("pulled back >2% from recent high")

    if vol_ratio > 1.5 and change_30m < 0:
        sell_pressure += 15
        reasons.append("selling volume elevated")

    sell_pressure = min(100, sell_pressure)

    if sell_pressure >= 75:
        verdict = "🔴 Exit Candidate"
    elif sell_pressure >= 50:
        verdict = "🟠 Trim / Tighten Stop"
    elif sell_pressure >= 30:
        verdict = "🟡 Watch Closely"
    else:
        verdict = "🟢 Hold / No Sell Signal"

    return {
        "symbol": symbol,
        "price": round(price, 2),
        "sell_pressure": sell_pressure,
        "verdict": verdict,
        "change_30m_pct": round(change_30m, 2),
        "change_60m_pct": round(change_60m, 2),
        "pullback_from_high_pct": round(pullback_from_high, 2),
        "volume_ratio": round(vol_ratio, 2),
        "reasons": reasons,
    }


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = []

    print("Ponder Sell Intelligence v1")
    print("===========================")

    for symbol in WATCH:
        try:
            print("Analyzing", symbol)
            r = analyze_symbol(symbol)
            if r:
                results.append(r)
        except Exception as e:
            print("ERROR", symbol, e)

    results = sorted(results, key=lambda x: x["sell_pressure"], reverse=True)

    payload = {
        "updated_at": now,
        "status": "research_only",
        "sell_candidates": results,
        "top_exit_candidate": results[0] if results else {},
        "notes": [
            "Research-only sell pressure analysis. Does not place trades.",
            "Use this to compare against live positions before connecting to bot.",
            "Best next step: log actual sell outcomes so sell rules can be backtested."
        ],
    }

    latest = OUT / "sell_intelligence_latest.json"
    latest.write_text(json.dumps(payload, indent=2))

    archive = OUT / f"sell_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    archive.write_text(json.dumps(payload, indent=2))

    print("Saved:", latest)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
