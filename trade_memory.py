import csv
import os
from datetime import datetime

TRADE_LOG_FILE = "trade_history.csv"

FIELDS = [
    "timestamp",
    "symbol",
    "side",
    "qty",
    "price",
    "reason",
    "score",
    "pnl",
    "pnl_pct",
]

def record_trade(symbol, side, qty, price, reason="", score=None, pnl=None, pnl_pct=None):
    file_exists = os.path.exists(TRADE_LOG_FILE)

    with open(TRADE_LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": price,
            "reason": reason,
            "score": score,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
        })


def recent_trade_count_today():
    if not os.path.exists(TRADE_LOG_FILE):
        return 0

    today = datetime.now().date().isoformat()
    count = 0

    with open(TRADE_LOG_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["timestamp"].startswith(today):
                count += 1

    return count


def symbol_traded_today(symbol):
    if not os.path.exists(TRADE_LOG_FILE):
        return False

    today = datetime.now().date().isoformat()

    with open(TRADE_LOG_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["timestamp"].startswith(today) and row["symbol"] == symbol:
                return True

    return False
