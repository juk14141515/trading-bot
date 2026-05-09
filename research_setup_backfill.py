"""Historical setup backfill for Ponder Invest AI.

Research-only. Downloads OHLCV data with yfinance, detects multiple setup
families, and writes labeled rows to research_data/*.csv. It never imports
bot.py and never places orders.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

import yfinance as yf

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "research_data"
SUMMARY_OUT = ROOT / "static" / "research" / "setup_backfill_latest.json"

ETF_SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "SMH", "ARKK"]
CRYPTO_SYMBOLS = ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"]
DAY_TRADE_SYMBOLS = ["NVDA", "AMD", "TSLA", "AAPL", "MSFT", "META", "PLTR", "SOFI", "HOOD", "COIN", "U"]
SMALL_CAP_SYMBOLS = ["U", "SOFI", "PLTR", "RBLX", "DKNG", "ROKU", "UPST", "AFRM", "HOOD"]
LARGE_CAP_SYMBOLS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "NFLX", "ORCL", "AMD"]
IPO_RECENT_SYMBOLS = ["ARM", "CAVA", "KVUE", "CART", "BIRK", "RDDT", "ALAB", "RBRK"]
EARNINGS_PROXY_SYMBOLS = ["NVDA", "AMD", "META", "TSLA", "NFLX", "AMZN", "GOOGL", "MSFT", "AAPL"]

FIELDS = [
    "timestamp", "symbol", "setup_type", "score", "entry_price", "market_regime", "reason",
    "next_1h_return", "next_1d_return", "next_3d_return", "next_5d_return", "outcome", "source"
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_float(x, default=0.0) -> float:
    try:
        if hasattr(x, "iloc"):
            if len(x) == 0:
                return default
            x = x.iloc[0]
        return float(x)
    except Exception:
        return default


def pct(a, b) -> float:
    try:
        if a == 0:
            return 0.0
        return round(((b - a) / a) * 100, 3)
    except Exception:
        return 0.0


def outcome_from_returns(r1d: float, r3d: float, r5d: float) -> str:
    best = max(r1d, r3d, r5d)
    worst = min(r1d, r3d, r5d)
    if best >= 4:
        return "winner"
    if worst <= -4:
        return "loser"
    if best >= 2 and worst > -3:
        return "missed_opportunity"
    if abs(r5d) < 1:
        return "flat"
    if r1d <= -2 and r5d > 1:
        return "early_exit"
    if r1d >= 2 and r5d < -1:
        return "late_exit"
    return "false_signal" if r5d < 0 else "flat"


def market_regime_from_close(close) -> str:
    if len(close) < 60:
        return "unknown"
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()

    latest = safe_float(close.iloc[-1])
    s20 = safe_float(sma20.iloc[-1])
    s50 = safe_float(sma50.iloc[-1])

    if latest > s20 > s50:
        return "bullish"
    if latest < s20 < s50:
        return "bearish"
    return "neutral"


def download(symbol: str, period: str = "24mo", interval: str = "1d"):
    try:
        data = yf.download(symbol, period=period, interval=interval, auto_adjust=True, progress=False)
        if data is None or data.empty:
            return None
        if isinstance(data.columns, type(getattr(data.columns, "droplevel", None))) and getattr(data.columns, "nlevels", 1) > 1:
            data.columns = data.columns.get_level_values(0)
        data = data.dropna()
        return data if len(data) >= 80 else None
    except Exception:
        return None


def row_for(data, i: int, symbol: str, setup_type: str, score: float, reason: str, source: str) -> Dict[str, object]:
    close = data["Close"]
    entry = safe_float(close.iloc[i])
    r1 = pct(entry, safe_float(close.iloc[min(i + 1, len(close) - 1)]))
    r3 = pct(entry, safe_float(close.iloc[min(i + 3, len(close) - 1)]))
    r5 = pct(entry, safe_float(close.iloc[min(i + 5, len(close) - 1)]))
    return {
        "timestamp": str(data.index[i]),
        "symbol": symbol,
        "setup_type": setup_type,
        "score": round(score, 2),
        "entry_price": round(entry, 4),
        "market_regime": market_regime_from_close(close.iloc[max(0, i - 60):i + 1]),
        "reason": reason,
        "next_1h_return": "",
        "next_1d_return": r1,
        "next_3d_return": r3,
        "next_5d_return": r5,
        "outcome": outcome_from_returns(r1, r3, r5),
        "source": source,
    }


def detect_setups(symbol: str, setup_type: str, data, source: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    close = data["Close"]
    volume = data["Volume"] if "Volume" in data else close * 0
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    vol20 = volume.rolling(20).mean()
    ret1 = close.pct_change() * 100
    ret5 = close.pct_change(5) * 100

    for i in range(60, len(data) - 6):
        price = safe_float(close.iloc[i])
        if price <= 0:
            continue
        c = safe_float(close.iloc[i])
        s20 = safe_float(sma20.iloc[i])
        s50 = safe_float(sma50.iloc[i])
        v = safe_float(volume.iloc[i])
        v20 = safe_float(vol20.iloc[i])
        r1 = safe_float(ret1.iloc[i])
        r5 = safe_float(ret5.iloc[i])
        prior_20_high = safe_float(close.iloc[i - 20:i].max())

        trend_bull = c > s20 > s50
        pullback = trend_bull and -4 <= r5 <= -1 and c >= s50
        breakout = trend_bull and c >= prior_20_high and v >= v20 * 1.1
        gap_move = abs(r1) >= 3
        momentum = r5 >= 4 and v >= v20 * 1.2

        if setup_type == "etf_trend" and trend_bull:
            rows.append(row_for(data, i, symbol, setup_type, 70 + min(20, r5), "ETF bullish 20/50 trend", source))
        elif setup_type == "crypto_momentum" and momentum:
            rows.append(row_for(data, i, symbol, setup_type, 72 + min(20, r5), "Crypto 5-day momentum with volume", source))
        elif setup_type == "day_trade_momentum" and momentum:
            rows.append(row_for(data, i, symbol, setup_type, 75 + min(20, r5), "Fast momentum proxy", source))
        elif setup_type == "small_cap_breakout" and breakout:
            rows.append(row_for(data, i, symbol, setup_type, 70 + min(20, r5), "Breakout with volume expansion", source))
        elif setup_type == "large_cap_pullback" and pullback:
            rows.append(row_for(data, i, symbol, setup_type, 68 + min(12, abs(r5)), "Large-cap pullback in bullish trend", source))
        elif setup_type == "gap_up_gap_down" and gap_move:
            rows.append(row_for(data, i, symbol, setup_type, 65 + min(25, abs(r1)), "Large 1-day gap/move proxy", source))
        elif setup_type == "earnings_reaction" and gap_move and v >= v20 * 1.3:
            rows.append(row_for(data, i, symbol, setup_type, 70 + min(20, abs(r1)), "Earnings/news reaction proxy: gap plus volume", source))
        elif setup_type == "ipo_recent" and i < 180 and momentum:
            rows.append(row_for(data, i, symbol, setup_type, 70 + min(20, r5), "Recent IPO momentum proxy", source))
    return rows


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run_group(name: str, symbols: Iterable[str], setup_type: str) -> Dict[str, object]:
    rows: List[Dict[str, object]] = []
    for symbol in symbols:
        data = download(symbol)
        if data is not None:
            rows.extend(detect_setups(symbol, setup_type, data, source="historical_backfill"))
    out = OUT_DIR / f"{name}.csv"
    write_csv(out, rows)
    return {"file": str(out), "rows": len(rows), "setup_type": setup_type}


def main() -> Dict[str, object]:
    groups = {
        "ipo_setups": (IPO_RECENT_SYMBOLS, "ipo_recent"),
        "etf_setups": (ETF_SYMBOLS, "etf_trend"),
        "crypto_setups": (CRYPTO_SYMBOLS, "crypto_momentum"),
        "daytrade_setups": (DAY_TRADE_SYMBOLS, "day_trade_momentum"),
        "smallcap_setups": (SMALL_CAP_SYMBOLS, "small_cap_breakout"),
        "largecap_pullback_setups": (LARGE_CAP_SYMBOLS, "large_cap_pullback"),
        "gap_setups": (DAY_TRADE_SYMBOLS + LARGE_CAP_SYMBOLS, "gap_up_gap_down"),
        "earnings_reaction_setups": (EARNINGS_PROXY_SYMBOLS, "earnings_reaction"),
    }
    results = {name: run_group(name, symbols, setup_type) for name, (symbols, setup_type) in groups.items()}
    summary = {"status": "ok", "generated_at": utc_now(), "groups": results, "total_rows": sum(v["rows"] for v in results.values())}
    SUMMARY_OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2, sort_keys=True))
    return summary


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
