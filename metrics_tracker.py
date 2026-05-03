
import csv
import os
from datetime import datetime

EQUITY_FILE = "equity_history.csv"
TRADE_FILE = "trade_history.csv"

def record_equity_snapshot(portfolio_value, buying_power, open_pl=0):
    file_exists = os.path.exists(EQUITY_FILE)

    with open(EQUITY_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "portfolio_value", "buying_power", "open_pl"
        ])

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "timestamp": datetime.now().isoformat(),
            "portfolio_value": portfolio_value,
            "buying_power": buying_power,
            "open_pl": open_pl,
        })
