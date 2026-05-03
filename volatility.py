import yfinance as yf
import pandas as pd


def get_atr(symbol, period="14d", interval="1d"):
    try:
        data = yf.download(
            symbol,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True
        )

        if data.empty or len(data) < 14:
            return None

        high = data["High"].squeeze()
        low = data["Low"].squeeze()
        close = data["Close"].squeeze()

        prev_close = close.shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.tail(14).mean()

        return round(float(atr), 2)

    except Exception as e:
        print(f"ATR error for {symbol}: {e}")
        return None


def calculate_position_size(account_equity, risk_percent, entry_price, atr, atr_multiplier=2):
    try:
        if atr is None or atr <= 0:
            return 0

        risk_dollars = account_equity * risk_percent
        stop_distance = atr * atr_multiplier

        shares = int(risk_dollars / stop_distance)
        max_affordable = int(account_equity / entry_price)

        return max(0, min(shares, max_affordable))

    except Exception as e:
        print(f"Position sizing error: {e}")
        return 0
