"""
Research-only historical backtest for the current Ponder Invest AI bot setup.

This approximates the current bot's live entry logic using historical price data:
- SPY must be bullish using SMA20 > SMA50 trend gate.
- Symbol must be bullish using SMA20 > SMA50 trend gate.
- Score uses the same weighted scoring function, but analyst/news are neutral
  because point-in-time historical analyst/news data is not available here.
- No orders are placed. No live trading code is changed.

Manual run:
    python3 current_strategy_backtest.py
    python3 current_strategy_backtest.py --period 2y --max-symbols 20

Output:
    static/research/current_strategy_backtest_latest.json
"""

from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None

from scoring_engine import calculate_weighted_score

ROOT = Path(__file__).resolve().parent
RESEARCH_DIR = ROOT / "static" / "research"
OUTPUT_FILE = RESEARCH_DIR / "current_strategy_backtest_latest.json"

WATCHLIST = [
    "AAPL", "AMZN", "NVDA", "MSFT", "GOOGL", "META", "TSLA", "AMD",
    "PLTR", "SOFI", "COIN", "RBLX", "U", "NFLX", "ORCL", "UBER",
    "SHOP", "PYPL", "SQ", "HOOD", "AFRM", "NET", "DDOG", "CRWD",
    "PANW", "ZS", "MDB", "APP", "UPST", "DKNG", "ROKU", "F", "GM",
    "T", "DIS",
]

MIN_SCORE_TO_TRADE = 63
TAKE_PROFIT_PERCENT = 0.12
STOP_LOSS_PERCENT = -0.06
MAX_POSITIONS_PER_DAY = 3


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    os.replace(tmp, path)


def clean_number(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return default
        return value
    except Exception:
        return default


def download_daily(symbol: str, period: str):
    if yf is None or pd is None:
        return None
    try:
        data = yf.download(symbol, period=period, interval="1d", auto_adjust=True, progress=False, threads=False)
    except Exception:
        return None
    if data is None or data.empty or "Close" not in data:
        return None
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [c[0] for c in data.columns]
    data = data.dropna(subset=["Close"]).copy()
    data["SMA20"] = data["Close"].rolling(20).mean()
    data["SMA50"] = data["Close"].rolling(50).mean()
    data["momentum_5d_pct"] = data["Close"].pct_change(5) * 100
    if "Volume" in data:
        data["volume_ratio"] = data["Volume"] / data["Volume"].rolling(20).mean()
    else:
        data["volume_ratio"] = 1.0
    return data


def is_bullish(row: Any) -> bool:
    close = clean_number(row.get("Close"), None)
    sma20 = clean_number(row.get("SMA20"), None)
    sma50 = clean_number(row.get("SMA50"), None)
    return bool(close and sma20 and sma50 and close > sma20 > sma50)


def momentum_score(momentum_5d_pct: Optional[float]) -> float:
    if momentum_5d_pct is None:
        return 50.0
    # Convert roughly -5%..+5% into 0..100.
    return max(0.0, min(100.0, 50.0 + momentum_5d_pct * 10.0))


def evaluate_exit(data: Any, entry_idx: int, entry_price: float) -> Dict[str, Any]:
    returns: Dict[str, Optional[float]] = {"30m": None, "1h": None, "1d": None, "5d": None}
    labels: Dict[str, str] = {"30m": "not_available_daily_data", "1h": "not_available_daily_data"}

    for label, offset in (("1d", 1), ("5d", 5)):
        if entry_idx + offset < len(data):
            exit_price = clean_number(data.iloc[entry_idx + offset].get("Close"), None)
            if exit_price and entry_price:
                ret = (exit_price - entry_price) / entry_price
                returns[label] = round(ret, 6)
                labels[label] = "win" if ret > 0 else "loss" if ret < 0 else "flat"
        else:
            labels[label] = "not_enough_future_data"

    stop_hit = False
    take_profit_hit = False
    max_drawdown = 0.0
    max_runup = 0.0
    for i in range(entry_idx + 1, min(entry_idx + 6, len(data))):
        high = clean_number(data.iloc[i].get("High"), None) or clean_number(data.iloc[i].get("Close"), None)
        low = clean_number(data.iloc[i].get("Low"), None) or clean_number(data.iloc[i].get("Close"), None)
        if high:
            max_runup = max(max_runup, (high - entry_price) / entry_price)
        if low:
            drawdown = (low - entry_price) / entry_price
            max_drawdown = min(max_drawdown, drawdown)
            if drawdown <= STOP_LOSS_PERCENT:
                stop_hit = True
        if max_runup >= TAKE_PROFIT_PERCENT:
            take_profit_hit = True

    return {
        "returns": returns,
        "labels": labels,
        "max_drawdown_5d": round(max_drawdown, 6),
        "max_runup_5d": round(max_runup, 6),
        "stop_loss_hit_5d": stop_hit,
        "take_profit_hit_5d": take_profit_hit,
    }


def summarize(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    evaluated_1d = [e for e in events if e.get("returns", {}).get("1d") is not None]
    evaluated_5d = [e for e in events if e.get("returns", {}).get("5d") is not None]

    def bucket(rows: List[Dict[str, Any]], horizon: str) -> Dict[str, Any]:
        rets = [clean_number(r.get("returns", {}).get(horizon), None) for r in rows]
        rets = [r for r in rets if r is not None]
        wins = [r for r in rets if r > 0]
        losses = [r for r in rets if r < 0]
        return {
            "sample_count": len(rets),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round((len(wins) / len(rets)) * 100, 2) if rets else None,
            "avg_return_pct": round((sum(rets) / len(rets)) * 100, 4) if rets else None,
            "best_return_pct": round(max(rets) * 100, 4) if rets else None,
            "worst_return_pct": round(min(rets) * 100, 4) if rets else None,
        }

    by_symbol: Dict[str, Dict[str, Any]] = {}
    for symbol in sorted({e["symbol"] for e in events}):
        rows = [e for e in events if e["symbol"] == symbol]
        by_symbol[symbol] = bucket(rows, "5d")

    return {
        "total_signals": len(events),
        "horizons": {
            "1d": bucket(evaluated_1d, "1d"),
            "5d": bucket(evaluated_5d, "5d"),
            "30m": {"sample_count": 0, "note": "Use forward simulator for intraday windows."},
            "1h": {"sample_count": 0, "note": "Use forward simulator for intraday windows."},
        },
        "by_symbol_5d": by_symbol,
        "best_examples": sorted(events, key=lambda e: e.get("returns", {}).get("5d") if e.get("returns", {}).get("5d") is not None else -999, reverse=True)[:10],
        "worst_examples": sorted(events, key=lambda e: e.get("returns", {}).get("5d") if e.get("returns", {}).get("5d") is not None else 999)[:10],
    }


def run_backtest(period: str = "1y", max_symbols: Optional[int] = None) -> Dict[str, Any]:
    symbols = WATCHLIST[:max_symbols] if max_symbols else WATCHLIST
    spy = download_daily("SPY", period)
    if spy is None or spy.empty:
        output = {
            "updated_at": iso_now(),
            "status": "error",
            "error": "Could not load SPY data.",
            "events": [],
            "summary": {},
        }
        write_json(OUTPUT_FILE, output)
        return output

    events: List[Dict[str, Any]] = []
    data_by_symbol = {symbol: download_daily(symbol, period) for symbol in symbols}

    for idx in range(55, len(spy) - 1):
        date = spy.index[idx]
        spy_row = spy.iloc[idx]
        if not is_bullish(spy_row):
            continue

        daily_candidates: List[Dict[str, Any]] = []
        for symbol, data in data_by_symbol.items():
            if data is None or data.empty or date not in data.index:
                continue
            symbol_idx = data.index.get_loc(date)
            if isinstance(symbol_idx, slice) or symbol_idx < 55 or symbol_idx >= len(data) - 1:
                continue
            row = data.iloc[symbol_idx]
            if not is_bullish(row):
                continue

            mom = clean_number(row.get("momentum_5d_pct"), 0.0)
            score = calculate_weighted_score(
                trend_score=100,
                analyst_score=50,
                news_score=50,
                momentum_score=momentum_score(mom),
                volatility_score=50,
            )
            if score < MIN_SCORE_TO_TRADE:
                continue
            daily_candidates.append(
                {
                    "symbol": symbol,
                    "score": score,
                    "momentum_5d_pct": round(mom or 0.0, 4),
                    "volume_ratio": round(clean_number(row.get("volume_ratio"), 1.0) or 1.0, 4),
                    "entry_idx": symbol_idx,
                    "entry_price": clean_number(row.get("Close"), None),
                    "data": data,
                }
            )

        daily_candidates.sort(key=lambda c: (c["score"], c["momentum_5d_pct"], c["volume_ratio"]), reverse=True)
        for candidate in daily_candidates[:MAX_POSITIONS_PER_DAY]:
            entry_price = candidate.get("entry_price")
            if not entry_price:
                continue
            exit_eval = evaluate_exit(candidate["data"], candidate["entry_idx"], entry_price)
            events.append(
                {
                    "strategy": "current_bot_price_only_approximation",
                    "symbol": candidate["symbol"],
                    "entry_time": str(date),
                    "entry_price": round(entry_price, 4),
                    "score": candidate["score"],
                    "conditions": {
                        "spy_trend": "bullish",
                        "symbol_trend": "bullish",
                        "analyst_score_assumption": "neutral_50_no_point_in_time_history",
                        "news_score_assumption": "neutral_50_no_point_in_time_history",
                        "momentum_5d_pct": candidate["momentum_5d_pct"],
                        "volume_ratio": candidate["volume_ratio"],
                    },
                    **exit_eval,
                }
            )

    output = {
        "updated_at": iso_now(),
        "version": "v1_current_strategy_price_only_backtest",
        "status": "research_only",
        "period": period,
        "symbols_tested": symbols,
        "limitations": [
            "This is a price-only approximation of the live bot strategy.",
            "Historical analyst/news recommendations are not point-in-time here, so analyst/news are neutralized at 50.",
            "30m and 1h windows are handled by the forward simulator, not this daily backtest.",
            "No live trading behavior is changed by this file.",
        ],
        "summary": summarize(events),
        "events": events,
    }
    write_json(OUTPUT_FILE, output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Research-only backtest of current bot setup.")
    parser.add_argument("--period", default="1y", help="yfinance period, for example 6mo, 1y, 2y, 5y")
    parser.add_argument("--max-symbols", type=int, default=None, help="Limit symbols for faster test runs")
    args = parser.parse_args()
    output = run_backtest(period=args.period, max_symbols=args.max_symbols)
    summary = output.get("summary", {})
    print("Ponder current strategy backtest complete")
    print(f"status: {output.get('status')}")
    print(f"signals: {summary.get('total_signals', 0)}")
    print(f"5d win rate: {summary.get('horizons', {}).get('5d', {}).get('win_rate')}")
    print(f"updated: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
