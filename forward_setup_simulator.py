"""
Research-only forward simulator for setups and current bot logic.

Runs during market hours (cron) and logs simulated entries. Later runs
resolve outcomes using latest available prices.

Output:
    static/research/forward_setup_simulations_latest.json
"""

from __future__ import annotations

import json
import os
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yfinance as yf
except Exception:
    yf = None

ROOT = Path(__file__).resolve().parent
RESEARCH_DIR = ROOT / "static" / "research"
OUTPUT_FILE = RESEARCH_DIR / "forward_setup_simulations_latest.json"

WATCHLIST = ["AAPL", "AMZN", "NVDA", "MSFT", "TSLA", "META", "AMD", "PLTR"]

HORIZONS = {
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "1d": timedelta(days=1),
}


def now() -> datetime:
    return datetime.now(timezone.utc)


def read_json() -> Dict[str, Any]:
    if not OUTPUT_FILE.exists():
        return {"records": []}
    try:
        return json.loads(OUTPUT_FILE.read_text())
    except Exception:
        return {"records": []}


def write_json(data: Dict[str, Any]) -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, OUTPUT_FILE)


def clean_float(value: Any) -> Optional[float]:
    try:
        # Handles pandas scalar, single-element Series, numpy values, strings.
        if hasattr(value, "iloc"):
            value = value.iloc[0]
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return None
        return number
    except Exception:
        return None


def latest_price(symbol: str) -> Optional[float]:
    if yf is None:
        return None
    try:
        data = yf.download(
            symbol,
            period="1d",
            interval="5m",
            auto_adjust=True,
            progress=False,
            threads=False,
        )
        if data is None or data.empty or "Close" not in data:
            return None
        close = data["Close"].dropna()
        if close.empty:
            return None
        return clean_float(close.iloc[-1])
    except Exception:
        return None


def detect_setups(symbol: str, price: float) -> List[str]:
    setups: List[str] = []
    if price:
        setups.append("current_bot")
        setups.append("momentum")
    return setups


def already_logged(records: List[Dict[str, Any]], symbol: str, setup: str, horizon: str, t: datetime) -> bool:
    """Avoid duplicate rows if cron runs multiple times in the same 15-minute window."""
    bucket_start = t.replace(minute=(t.minute // 15) * 15, second=0, microsecond=0)
    bucket_end = bucket_start + timedelta(minutes=15)
    for row in records:
        if row.get("symbol") != symbol or row.get("setup") != setup or row.get("horizon") != horizon:
            continue
        try:
            entry_time = datetime.fromisoformat(str(row.get("entry_time")))
        except Exception:
            continue
        if bucket_start <= entry_time < bucket_end:
            return True
    return False


def run() -> None:
    data = read_json()
    records = data.get("records", [])
    if not isinstance(records, list):
        records = []

    t = now()
    generated = 0
    evaluated = 0

    # Generate new simulations.
    for symbol in WATCHLIST:
        price = latest_price(symbol)
        if not price:
            continue
        for setup in detect_setups(symbol, price):
            for horizon, delta in HORIZONS.items():
                if already_logged(records, symbol, setup, horizon, t):
                    continue
                records.append(
                    {
                        "symbol": symbol,
                        "setup": setup,
                        "entry_time": t.isoformat(),
                        "entry_price": round(price, 4),
                        "horizon": horizon,
                        "due_time": (t + delta).isoformat(),
                        "status": "pending",
                        "result": "Pending",
                    }
                )
                generated += 1

    # Evaluate existing simulations.
    for row in records:
        if row.get("status") != "pending":
            continue
        try:
            due = datetime.fromisoformat(str(row["due_time"]))
        except Exception:
            row["status"] = "unresolved"
            row["result"] = "Invalid due time"
            continue
        if now() < due:
            continue
        price = latest_price(str(row.get("symbol", "")))
        entry = clean_float(row.get("entry_price"))
        if not price or not entry:
            row["result"] = "Waiting for price data"
            continue
        ret = (price - entry) / entry
        row["exit_price"] = round(price, 4)
        row["return"] = round(ret, 6)
        row["return_pct"] = round(ret * 100, 4)
        row["status"] = "evaluated"
        row["result"] = "win" if ret > 0 else "loss" if ret < 0 else "flat"
        row["evaluated_at"] = now().isoformat()
        evaluated += 1

    evaluated_rows = [r for r in records if r.get("status") == "evaluated"]
    wins = [r for r in evaluated_rows if r.get("result") == "win"]
    returns = [clean_float(r.get("return")) for r in evaluated_rows]
    returns = [r for r in returns if r is not None]

    data["updated_at"] = t.isoformat()
    data["status"] = "research_only"
    data["summary"] = {
        "total_records": len(records),
        "pending": len([r for r in records if r.get("status") == "pending"]),
        "evaluated": len(evaluated_rows),
        "generated_now": generated,
        "evaluated_now": evaluated,
        "win_rate": round((len(wins) / len(evaluated_rows)) * 100, 2) if evaluated_rows else None,
        "avg_return_pct": round((sum(returns) / len(returns)) * 100, 4) if returns else None,
    }
    data["records"] = records[-5000:]
    write_json(data)

    print("Forward simulator complete")
    print(f"generated now: {generated}")
    print(f"evaluated now: {evaluated}")
    print(f"total records: {data['summary']['total_records']}")


if __name__ == "__main__":
    run()
