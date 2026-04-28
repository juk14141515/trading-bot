import alpaca_trade_api as tradeapi

API_KEY = "PK54UWSJEP5SMKSMLZMI4AQMLS"
SECRET_KEY = "6quBqLTFABUB5pbhjgaS4TsCdq8iUmXQWSXrNjRdofzp"
BASE_URL = "https://paper-api.alpaca.markets/v2"

api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL)

account = api.get_account()
positions = api.list_positions()

print("\n==============================")
print(" LIVE PAPER P/L DASHBOARD")
print("==============================")
print("Account status:", account.status)
print("Buying power:", account.buying_power)
print("Portfolio value:", account.portfolio_value)
print()

if not positions:
    print("No open positions.")
else:
    for p in positions:
        print(f"{p.symbol}")
        print(f"  Qty: {p.qty}")
        print(f"  Avg entry: ${p.avg_entry_price}")
        print(f"  Current: ${p.current_price}")
        print(f"  Unrealized P/L: ${p.unrealized_pl}")
        print(f"  Unrealized P/L %: {float(p.unrealized_plpc) * 100:.2f}%")
        print()

print("==============================")