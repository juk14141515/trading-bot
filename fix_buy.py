import re

with open("bot.py", "r") as f:
    content = f.read()

# New clean buy() function
new_buy_function = '''
def buy(symbol, score):
    price = float(api.get_latest_trade(symbol).price)

    atr = get_atr(symbol)

    shares = calculate_position_size(
        account_equity=float(api.get_account().equity),
        risk_percent=0.01,
        entry_price=price,
        atr=atr,
        atr_multiplier=2
    )

    if shares <= 0:
        log(f"SKIP BUY | {symbol} | invalid position size")
        return

    dollars = shares * price

    deployed = get_deployed_value()
    account = api.get_account()
    equity = float(account.equity)

    max_deployed = equity * MAX_TOTAL_DEPLOYED_PERCENT

    if deployed + dollars > max_deployed:
        log(f"SKIP BUY | {symbol} | would exceed max deployed")
        return

    log(f"BUY {symbol} | price={price:.2f} | ATR={atr} | shares={shares} | dollars={dollars:.2f}")

    api.submit_order(
        symbol=symbol,
        notional=dollars,
        side="buy",
        type="market",
        time_in_force="day"
    )

    print(f"BUY placed: {symbol} | ${dollars}")
    log(f"BUY | {symbol} | ${dollars} | score={score}")
    notify_discord(f"🟢 BUY PLACED | {symbol} | ${dollars:.2f} | score={score}")
'''

# Replace existing buy() function
updated = re.sub(
    r"def buy\(.*?\n\s*def ",
    new_buy_function + "\ndef ",
    content,
    flags=re.DOTALL
)

with open("bot.py", "w") as f:
    f.write(updated)

print("buy() function replaced successfully.")
