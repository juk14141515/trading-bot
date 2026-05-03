import json
from datetime import datetime, timedelta
from itertools import product

import pandas as pd
import yfinance as yf


SYMBOL_GROUPS = {
    "all": ["AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "GOOGL", "AMZN"],
    "strong_backtest": ["AMD", "NVDA", "GOOGL", "AMZN"],
    "semis": ["AMD", "NVDA"],
}

DAYS_BACK = 10
INTERVAL = "5m"

BUY_THRESHOLDS = [70, 72.5, 75, 77.5, 80]
TAKE_PROFITS = [0.015, 0.02, 0.025]
STOP_LOSSES = [-0.01, -0.015, -0.02]
MAX_HOLD_BARS_LIST = [6, 12]  # 30m, 60m


def flatten(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df.dropna()


def prepare_symbol(symbol):
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

    if df.empty:
        return None

    df = flatten(df)
    close = df["Close"].astype(float)

    change_30m = close.pct_change(6)

    momentum = pd.Series(50, index=df.index)
    momentum[change_30m > 0.02] = 90
    momentum[(change_30m > 0.01) & (change_30m <= 0.02)] = 75
    momentum[(change_30m > 0) & (change_30m <= 0.01)] = 60
    momentum[(change_30m > -0.01) & (change_30m <= 0)] = 45
    momentum[change_30m <= -0.01] = 25

    sma_short = close.rolling(5).mean()
    sma_long = close.rolling(20).mean()

    trend = pd.Series(50, index=df.index)
    trend[(close > sma_short) & (sma_short > sma_long)] = 85
    trend[(close > sma_long) & ~((close > sma_short) & (sma_short > sma_long))] = 65
    trend[(close < sma_short) & (sma_short < sma_long)] = 25

    df["score"] = (momentum * 0.55 + trend * 0.45).round(2)

    return df.dropna()


def simulate(data, symbols, threshold, tp, sl, max_hold):
    trades = []

    for symbol in symbols:
        df = data.get(symbol)
        if df is None or df.empty:
            continue

        closes = df["Close"].astype(float).tolist()
        scores = df["score"].tolist()

        for i in range(25, len(df) - max_hold):
            score = scores[i]
            if score < threshold:
                continue

            entry = closes[i]
            exit_price = closes[i + max_hold]
            exit_reason = "max_hold"

            for j in range(i + 1, i + max_hold + 1):
                pnl = (closes[j] - entry) / entry

                if pnl >= tp:
                    exit_price = closes[j]
                    exit_reason = "take_profit"
                    break

                if pnl <= sl:
                    exit_price = closes[j]
                    exit_reason = "stop_loss"
                    break

            pnl_pct = (exit_price - entry) / entry * 100
            trades.append((symbol, pnl_pct, exit_reason))

    if not trades:
        return None

    df = pd.DataFrame(trades, columns=["symbol", "pnl_pct", "exit_reason"])

    total = len(df)
    wins = int((df["pnl_pct"] > 0).sum())
    win_rate = wins / total * 100
    avg_pnl = df["pnl_pct"].mean()
    total_pnl = df["pnl_pct"].sum()
    worst = df["pnl_pct"].min()

    quality = (
        avg_pnl * 45
        + win_rate * 0.35
        + min(total, 250) * 0.03
        + total_pnl * 0.025
        + worst * 2
    )

    return {
        "threshold": threshold,
        "take_profit_pct": round(tp * 100, 2),
        "stop_loss_pct": round(sl * 100, 2),
        "max_hold_minutes": max_hold * 5,
        "trades": total,
        "wins": wins,
        "losses": total - wins,
        "win_rate": round(win_rate, 2),
        "avg_pnl_pct": round(avg_pnl, 4),
        "total_pnl_pct": round(total_pnl, 2),
        "worst_trade_pct": round(worst, 2),
        "quality_score": round(quality, 4),
    }


def main():
    all_symbols = sorted(set(sum(SYMBOL_GROUPS.values(), [])))

    print("Downloading/preparing data...")
    data = {}
    for symbol in all_symbols:
        print(symbol)
        prepared = prepare_symbol(symbol)
        if prepared is not None:
            data[symbol] = prepared

    results = []

    for group_name, symbols in SYMBOL_GROUPS.items():
        print(f"Optimizing {group_name}...")

        for threshold, tp, sl, hold in product(
            BUY_THRESHOLDS,
            TAKE_PROFITS,
            STOP_LOSSES,
            MAX_HOLD_BARS_LIST,
        ):
            result = simulate(data, symbols, threshold, tp, sl, hold)
            if result:
                result["symbols_group"] = group_name
                results.append(result)

    df = pd.DataFrame(results).sort_values("quality_score", ascending=False)
    df.to_csv("strategy_research_results_v2.csv", index=False)

    best = df.iloc[0].to_dict()
    with open("best_strategy_config_v2.json", "w") as f:
        json.dump(best, f, indent=2)

    print("\nTOP 10 SETUPS")
    print(df.head(10).to_string(index=False))
    print("\nSaved strategy_research_results_v2.csv")
    print("Saved best_strategy_config_v2.json")


if __name__ == "__main__":
    main()
