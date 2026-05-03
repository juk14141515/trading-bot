
import yfinance as yf

def get_enhanced_candidates():
    symbols = [
        "OPEN","SOFI","RIVN","LCID","CHPT",
        "MARA","RIOT","IONQ","RKLB","ACHR",
        "ASTS","SOUN","BBAI","JOBY","PLTR",
        "NVDA","AMD","TSLA","COIN","AI"
    ]

    candidates = []

    for symbol in symbols:
        try:
            data = yf.download(symbol, period="5d", interval="5m", progress=False)

            if data is None or len(data) < 50:
                continue

            close = data["Close"]
            volume = data["Volume"]

            price = float(close.iloc[-1])
            vol = float(volume.iloc[-1])
            avg_vol = float(volume.rolling(20).mean().iloc[-1])

            momentum = close.iloc[-1] > close.rolling(10).mean().iloc[-1]
            volume_spike = vol > avg_vol * 1.3

            if momentum and volume_spike:
                candidates.append(symbol)

        except:
            continue

    return candidates
