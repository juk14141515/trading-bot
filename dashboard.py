from collections import Counter
from datetime import datetime

LOG_FILE = "log.txt"

def read_logs():
    try:
        with open(LOG_FILE, "r") as f:
            return f.readlines()
    except FileNotFoundError:
        print("No log.txt found yet.")
        return []

def dashboard():
    lines = read_logs()

    buys = [line for line in lines if "| BUY |" in line]
    sells = [line for line in lines if "| SELL |" in line]
    cycles = [line for line in lines if "NEW CYCLE" in line]
    errors = [line for line in lines if "ERROR" in line]
    market_closed = [line for line in lines if "Market closed" in line]

    bought_symbols = []
    sold_symbols = []

    for line in buys:
        parts = line.strip().split("|")
        if len(parts) >= 3:
            bought_symbols.append(parts[2].strip())

    for line in sells:
        parts = line.strip().split("|")
        if len(parts) >= 3:
            sold_symbols.append(parts[2].strip())

    print("\n==============================")
    print(" BOT PERFORMANCE DASHBOARD")
    print("==============================")
    print("Last updated:", datetime.now())
    print()
    print("Total cycles:", len(cycles))
    print("Total buys:", len(buys))
    print("Total sells:", len(sells))
    print("Market closed cycles:", len(market_closed))
    print("Errors:", len(errors))
    print()

    print("Most bought:")
    for symbol, count in Counter(bought_symbols).most_common():
        print(f"  {symbol}: {count}")

    print()

    print("Most sold:")
    for symbol, count in Counter(sold_symbols).most_common():
        print(f"  {symbol}: {count}")

    print()

    print("Recent activity:")
    for line in lines[-10:]:
        print(" ", line.strip())

    print("==============================\n")

dashboard()