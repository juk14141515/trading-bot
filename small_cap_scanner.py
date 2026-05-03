import yfinance as yf


def get_small_cap_candidates():
    symbols = [
        "OPEN", "SOFI", "RIVN", "LCID", "CHPT",
        "MARA", "RIOT", "IONQ", "RKLB", "ACHR",
        "ASTS", "SOUN", "BBAI", "JOBY", "PLTR"
    ]

    candidates = []

    for symbol in symbols:
        try:
            data = yf.download(
                symbol,
                period="5d",
                interval="5m",
                progress=False,
                auto_adjust=True
            )

            if data is None or len(data) < 50:
                continue

            close = data["Close"].squeeze()
            volume = data["Volume"].squeeze()
            high = data["High"].squeeze()

            price = float(close.iloc[-1])
            current_volume = float(volume.iloc[-1])
            avg_volume = float(volume.rolling(20).mean().iloc[-1])

            short_ma = float(close.rolling(5).mean().iloc[-1])
            long_ma = float(close.rolling(20).mean().iloc[-1])

            previous_high = float(high.rolling(20).max().iloc[-2])

            price_ok = 2 <= price <= 30
            volume_spike = current_volume >= avg_volume * 1.5
            momentum_up = short_ma > long_ma
            near_breakout = price >= previous_high * 0.98
            breakout = price > previous_high

            print(
                f"{symbol} | price={price:.2f} | "
                f"vol={current_volume:.0f}/{avg_volume:.0f} | "
                f"momentum={momentum_up} | near={near_breakout} | breakout={breakout}"
            )

            if price_ok and volume_spike and momentum_up:
                if breakout:
                    print(f"🚀 BREAKOUT | {symbol} | price={price:.2f}")
                    candidates.append(symbol)
                elif near_breakout:
                    print(f"⚠️ NEAR BREAKOUT | {symbol} | price={price:.2f}")

        except Exception as e:
            print(f"Small-cap scanner error for {symbol}: {e}")

    return candidates
