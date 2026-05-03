from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

# Scanner v1 universe: liquid large/mega-cap names
SYMBOLS = [
    "AAPL", "MSFT", "NVDA", "AMD", "AMZN", "GOOGL", "META", "TSLA",
    "AVGO", "NFLX", "COST", "ADBE", "CRM", "ORCL", "INTC", "QCOM",
    "MU", "SMCI", "PLTR", "COIN", "UBER", "SHOP", "NOW", "PANW",
    "SNOW", "CRWD", "ARM", "TSM", "ASML", "QQQ", "SPY"
]

DAYS_BACK = 20
INTERVAL = "1d"

MIN_PRICE = 5
MIN_AVG_VOLUME = 1_000_000


def flatten(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df.dropna()


def score_symbol(symbol):
    end = datetime.now()
    start = end - timedelta(days=DAYS_BACK + 10)

    df = yf.download(
        symbol,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        interval=INTERVAL,
        progress=False,
        auto_adjust=True,
    )

    if df.empty or len(df) < 15:
        return None

    df = flatten(df)

    close = df["Close"].astype(float)
    volume = df["Volume"].astype(float)

    price = float(close.iloc[-1])
    avg_volume = float(volume.tail(10).mean())

    if price < MIN_PRICE or avg_volume < MIN_AVG_VOLUME:
        return None

    sma5 = float(close.tail(5).mean())
    sma20 = float(close.tail(20).mean()) if len(close) >= 20 else float(close.mean())

    change_1d = float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100)
    change_5d = float((close.iloc[-1] - close.iloc[-6]) / close.iloc[-6] * 100) if len(close) >= 6 else 0
    change_20d = float((close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100)

    vol_ratio = float(volume.iloc[-1] / avg_volume) if avg_volume else 1

    trend_score = 50
    if price > sma5 > sma20:
        trend_score = 90
    elif price > sma20:
        trend_score = 70
    elif price < sma5 < sma20:
        trend_score = 25

    momentum_score = 50
    if change_5d > 8:
        momentum_score = 95
    elif change_5d > 4:
        momentum_score = 80
    elif change_5d > 1:
        momentum_score = 65
    elif change_5d < -4:
        momentum_score = 25

    volume_score = 50
    if vol_ratio > 2:
        volume_score = 90
    elif vol_ratio > 1.3:
        volume_score = 75
    elif vol_ratio < 0.7:
        volume_score = 35

    final_score = round(
        trend_score * 0.45 +
        momentum_score * 0.40 +
        volume_score * 0.15,
        2
    )

    if final_score >= 80:
        label = "🔥 Strong Watch"
    elif final_score >= 70:
        label = "✅ Watch"
    elif final_score >= 60:
        label = "👀 Weak Watch"
    else:
        label = "Skip"

    return {
        "symbol": symbol,
        "price": round(price, 2),
        "final_score": final_score,
        "trend_score": trend_score,
        "momentum_score": momentum_score,
        "volume_score": volume_score,
        "change_1d_pct": round(change_1d, 2),
        "change_5d_pct": round(change_5d, 2),
        "change_20d_pct": round(change_20d, 2),
        "volume_ratio": round(vol_ratio, 2),
        "avg_volume": int(avg_volume),
        "label": label,
    }


def main():
    results = []

    print("Ponder Market Scanner v1")
    print("========================")

    for symbol in SYMBOLS:
        try:
            print(f"Scanning {symbol}...")
            result = score_symbol(symbol)
            if result:
                results.append(result)
        except Exception as e:
            print(f"ERROR {symbol}: {e}")

    if not results:
        print("No scanner results.")
        return

    df = pd.DataFrame(results)
    df = df.sort_values("final_score", ascending=False)

    df.to_csv("market_scanner_results_v1.csv", index=False)
    df.head(10).to_json("top_10_candidates_v1.json", orient="records", indent=2)

    print("\nTOP 15 OPPORTUNITIES")
    print(df.head(15).to_string(index=False))

    print("\nSaved:")
    print("- market_scanner_results_v1.csv")
    print("- top_10_candidates_v1.json")


if __name__ == "__main__":
    main()
