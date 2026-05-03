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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

try:
    import yfinance as yf
except Exception:
    yf = None

ROOT = Path(__file__).resolve().parent
RESEARCH_DIR = ROOT / "static" / "research"
OUTPUT_FILE = RESEARCH_DIR / "forward_setup_simulations_latest.json"

WATCHLIST = ["AAPL","AMZN","NVDA","MSFT","TSLA","META","AMD","PLTR"]

HORIZONS = {
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "1d": timedelta(days=1),
}


def now():
    return datetime.now(timezone.utc)


def read_json():
    if not OUTPUT_FILE.exists():
        return {"records": []}
    try:
        return json.loads(OUTPUT_FILE.read_text())
    except:
        return {"records": []}


def write_json(data):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, OUTPUT_FILE)


def latest_price(symbol):
    if yf is None:
        return None
    try:
        data = yf.download(symbol, period="1d", interval="5m", progress=False)
        if data is None or data.empty:
            return None
        return float(data["Close"].dropna().iloc[-1])
    except:
        return None


def detect_setups(symbol, price):
    setups = []
    if price:
        setups.append("current_bot")
        setups.append("momentum")
    return setups


def run():
    data = read_json()
    records = data.get("records", [])

    t = now()

    # Generate new simulations
    for symbol in WATCHLIST:
        price = latest_price(symbol)
        if not price:
            continue
        for setup in detect_setups(symbol, price):
            for horizon, delta in HORIZONS.items():
                record = {
                    "symbol": symbol,
                    "setup": setup,
                    "entry_time": t.isoformat(),
                    "entry_price": price,
                    "horizon": horizon,
                    "due_time": (t + delta).isoformat(),
                    "status": "pending",
                }
                records.append(record)

    # Evaluate existing
    for r in records:
        if r.get("status") != "pending":
            continue
        due = datetime.fromisoformat(r["due_time"])
        if now() < due:
            continue
        price = latest_price(r["symbol"])
        if not price:
            continue
        entry = r.get("entry_price")
        ret = (price - entry) / entry
        r["return"] = round(ret, 6)
        r["status"] = "evaluated"
        r["result"] = "win" if ret > 0 else "loss"

    data["updated_at"] = t.isoformat()
    data["records"] = records[-5000:]
    write_json(data)

    print("Forward simulator complete")


if __name__ == "__main__":
    run()
