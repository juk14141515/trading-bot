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
TAKE_PROFITS = [0.015, 0.02, 0.025, 0.03]
STOP_LOSSES = [-0.01, -0.015, -0.02]
MAX_HOLD_BARS_LIST = [6, 12, 18]  # 30m, 60m, 90m


def flatten_yfinance(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df.dropna()


def momentum_score(df, i):
    if i < 6:
        return 50
    current = float(df["Close"].iloc[i])
    past = float(df["Close"].iloc[i - 6])
    change = (current - past) / past

    if change > 0.02:
        return 90
    if change > 0.01:
        return 75
    if change > 0:
        return 60
    if change > -0.01:
        return 45
    return 25


def trend_score(df, i):
    if i < 20:
        return 50

    close = float(df["Close"].iloc[i])
    sma_short = float(df["Close"].iloc[i - 5:i].mean())
    sma_long = float(df["Close"].iloc[i - 20:i].mean())

    if close > sma_short > sma_long:
        return 85
    if close > sma_long:
        return 65
    if close < sma_short < sma_long:
        return 25
    return 50


def final_score(df, i):
    m = momentum_score(df, i)
    t = trend_score(df, i)
    return round((m * 0.55) + (t * 0.45), 2)


def download_data(symbols):
    data = {}
    end = datetime.now()
    start = end - timedelta(days=DAYS_BACK)

    for symbol in symbols:
        print(f"Downloading {symbol}...")
        df = yf.download(
            symbol,
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            interval=INTERVAL,
            progress=False,
            auto_adjust=True,
        )

        if not df.empty:
            data[symbol] = flatten_yfinance(df)

    return data


def simulate_config(data, symbols, threshold, tp, sl, max_hold_bars):
    trades = []

    for symbol in symbols:
        df = data.get(symbol)
        if df is None or df.empty:
            continue

        for i in range(25, len(df) - max_hold_bars):
            score = final_score(df, i)
            if score < threshold:
                continue

            entry_price = float(df["Close"].iloc[i])
            exit_price = None
            exit_reason = "max_hold"

            for j in range(i + 1, min(i + max_hold_bars + 1, len(df))):
                price = float(df["Close"].iloc[j])
                pnl_pct = (price - entry_price) / entry_price

                if pnl_pct >= tp:
                    exit_price = price
                    exit_reason = "take_profit"
                    break

                if pnl_pct <= sl:
                    exit_price = price
                    exit_reason = "stop_loss"
                    break

            if exit_price is None:
                exit_price = float(df["Close"].iloc[i + max_hold_bars])

            pnl_pct = (exit_price - entry_price) / entry_price

            trades.append({
                "symbol": symbol,
                "score": score,
                "pnl_pct": pnl_pct * 100,
                "result": "WIN" if pnl_pct > 0 else "LOSS",
                "exit_reason": exit_reason,
            })

    if not trades:
        return None

    df = pd.DataFrame(trades)

    wins = int((df["result"] == "WIN").sum())
    total = len(df)
    losses = total - wins
    win_rate = wins / total * 100
    avg_pnl = df["pnl_pct"].mean()
    total_pnl = df["pnl_pct"].sum()
    worst_trade = df["pnl_pct"].min()

    # Simple quality score: rewards edge, penalizes too few trades and big losses.
    quality_score = (
        avg_pnl * 45
        + win_rate * 0.35
        + min(total, 300) * 0.03
        + total_pnl * 0.03
        + worst_trade * 2
    )

    return {
        "symbols_group": None,
        "threshold": threshold,
        "take_profit_pct": round(tp * 100, 2),
        "stop_loss_pct": round(sl * 100, 2),
        "max_hold_minutes": max_hold_bars * 5,
        "trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "avg_pnl_pct": round(avg_pnl, 4),
        "total_pnl_pct": round(total_pnl, 2),
        "worst_trade_pct": round(worst_trade, 2),
        "quality_score": round(quality_score, 4),
    }


def main():
    all_symbols = sorted(set(sum(SYMBOL_GROUPS.values(), [])))
    data = download_data(all_symbols)

    results = []

    for group_name, symbols in SYMBOL_GROUPS.items():
        print(f"\nOptimizing group: {group_name}")

        for threshold, tp, sl, max_hold in product(
            BUY_THRESHOLDS,
            TAKE_PROFITS,
            STOP_LOSSES,
            MAX_HOLD_BARS_LIST,
        ):
            result = simulate_config(data, symbols, threshold, tp, sl, max_hold)

            if result:
                result["symbols_group"] = group_name
                results.append(result)

    if not results:
        print("No results found.")
        return

    df = pd.DataFrame(results)
    df = df.sort_values("quality_score", ascending=False)

    df.to_csv("strategy_research_results_v1.csv", index=False)

    best = df.iloc[0].to_dict()
    with open("best_strategy_config_v1.json", "w") as f:
        json.dump(best, f, indent=2)

    print("\n==============================")
    print("PONDER STRATEGY OPTIMIZER V1")
    print("==============================")
    print("\nTop 10 setups:")
    print(df.head(10).to_string(index=False))
    print("\nSaved:")
    print("- strategy_research_results_v1.csv")
    print("- best_strategy_config_v1.json")


if __name__ == "__main__":
    main()
