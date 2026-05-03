
import yfinance as yf

SCAN_SYMBOLS = [
    "AAPL","MSFT","NVDA","AMD","GOOGL","AMZN","META","TSLA",
    "PLTR","SOFI","COIN","RBLX","U","NFLX","ORCL","UBER",
    "SHOP","PYPL","SQ","HOOD","AFRM","NET","DDOG","CRWD",
    "PANW","ZS","MDB","APP","UPST","DKNG","ROKU","F","GM",
    "DIS","MARA","RIOT","IONQ","RKLB","ACHR","ASTS","SOUN",
    "BBAI","JOBY","OPEN","RIVN","LCID","CHPT"
]

def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default

def score_symbol(symbol):
    try:
        data = yf.download(
            symbol,
            period="10d",
            interval="15m",
            progress=False,
            auto_adjust=True
        )

        if data is None or len(data) < 40:
            return None

        close = data["Close"].squeeze()
        volume = data["Volume"].squeeze()
        high = data["High"].squeeze()

        price = _safe_float(close.iloc[-1])
        if price <= 0:
            return None

        vol_now = _safe_float(volume.iloc[-1])
        avg_vol = _safe_float(volume.rolling(20).mean().iloc[-1])
        avg_vol = max(avg_vol, 1)

        ma_fast = _safe_float(close.rolling(8).mean().iloc[-1])
        ma_slow = _safe_float(close.rolling(21).mean().iloc[-1])

        last = _safe_float(close.iloc[-1])
        prev = _safe_float(close.iloc[-6]) if len(close) > 6 else last
        momentum_pct = (last - prev) / prev if prev else 0

        previous_high = _safe_float(high.rolling(30).max().iloc[-2])
        near_breakout = previous_high > 0 and price >= previous_high * 0.985
        breakout = previous_high > 0 and price > previous_high

        volume_ratio = vol_now / avg_vol

        score = 0

        if ma_fast > ma_slow:
            score += 30

        if momentum_pct > 0.005:
            score += 20
        elif momentum_pct > 0:
            score += 10

        if volume_ratio >= 2.0:
            score += 25
        elif volume_ratio >= 1.3:
            score += 15

        if breakout:
            score += 25
        elif near_breakout:
            score += 15

        # avoid junky ultra-cheap names
        if price < 2:
            score -= 25

        # prefer tradable price ranges, but allow large caps too
        if 2 <= price <= 250:
            score += 10

        return {
            "symbol": symbol,
            "score": round(score, 2),
            "price": round(price, 2),
            "momentum_pct": round(momentum_pct * 100, 2),
            "volume_ratio": round(volume_ratio, 2),
            "breakout": breakout,
            "near_breakout": near_breakout,
        }

    except Exception:
        return None

def get_enhanced_candidates(limit=12, min_score=45):
    results = []

    for symbol in SCAN_SYMBOLS:
        result = score_symbol(symbol)
        if not result:
            continue

        if result["score"] >= min_score:
            results.append(result)

    results.sort(key=lambda x: x["score"], reverse=True)

    symbols = [r["symbol"] for r in results[:limit]]

    print("ENHANCED SCANNER RESULTS:", results[:limit])

    return symbols
