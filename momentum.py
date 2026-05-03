import yfinance as yf


def get_momentum_score(symbol):
    try:
        data = yf.download(
            symbol,
            period="5d",
            interval="30m",
            progress=False,
            auto_adjust=True
        )

        if len(data) < 10:
            return 50

        closes = data["Close"]

        short = float(closes.tail(5).mean().iloc[0])
        long = float(closes.tail(20).mean().iloc[0])

        if long == 0:
            return 50

        change = (short - long) / long

        score = 50 + (change * 500)

        score = max(0, min(100, score))

        return round(score, 2)

    except Exception as e:
        print(f"Momentum error for {symbol}: {e}")
        return 50
