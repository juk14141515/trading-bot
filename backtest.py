import yfinance as yf
import pandas as pd

def get_data(symbol="SPY", period="6mo", interval="1d"):
    return yf.download(symbol, period=period, interval=interval)

def sma_strategy(df):
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["SMA200"] = df["Close"].rolling(200).mean()

    df["signal"] = 0
    df.loc[df["SMA50"] > df["SMA200"], "signal"] = 1

    df["returns"] = df["Close"].pct_change()
    df["strategy"] = df["returns"] * df["signal"].shift(1)

    return df["strategy"].sum()

def rsi_strategy(df):
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    df["signal"] = 0
    df.loc[df["RSI"] < 30, "signal"] = 1
    df.loc[df["RSI"] > 70, "signal"] = -1

    df["returns"] = df["Close"].pct_change()
    df["strategy"] = df["returns"] * df["signal"].shift(1)

    return df["strategy"].sum()

def run_backtest():
    df = get_data()

    results = {
        "sma": sma_strategy(df.copy()),
        "rsi": rsi_strategy(df.copy())
    }

    best = max(results, key=results.get)

    print("Strategy results:", results)
    print("Best strategy:", best)

    return best

if __name__ == "__main__":
    run_backtest()
