from pathlib import Path
from datetime import datetime

BOT = Path("bot.py")

backup = Path(f"bot_backup_full_upgrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
backup.write_text(BOT.read_text())

# =========================
# EXIT MANAGER
# =========================
Path("exit_manager.py").write_text(r'''
def should_exit(position, get_trend):
    symbol = position.symbol
    entry = float(position.avg_entry_price)
    current = float(position.current_price)

    change = (current - entry) / entry

    # Hard stop / TP handled elsewhere
    # Add smarter exits

    # 1. Trailing stop (lock profits)
    if change > 0.04 and change < 0.02:
        return True, "trailing stop"

    # 2. Dead trade (no movement)
    if abs(change) < 0.01:
        return True, "no momentum"

    # 3. Weak trend
    if get_trend(symbol) == "neutral" and change < 0:
        return True, "weak trend"

    return False, None
''')

# =========================
# ENHANCED SCANNER
# =========================
Path("enhanced_scanner.py").write_text(r'''
import yfinance as yf

def get_enhanced_candidates():
    symbols = [
        "OPEN","SOFI","RIVN","LCID","CHPT",
        "MARA","RIOT","IONQ","RKLB","ACHR",
        "ASTS","SOUN","BBAI","JOBY","PLTR",
        "NVDA","AMD","TSLA","COIN","AI"
    ]

    candidates = []

    for symbol in symbols:
        try:
            data = yf.download(symbol, period="5d", interval="5m", progress=False)

            if data is None or len(data) < 50:
                continue

            close = data["Close"]
            volume = data["Volume"]

            price = float(close.iloc[-1])
            vol = float(volume.iloc[-1])
            avg_vol = float(volume.rolling(20).mean().iloc[-1])

            momentum = close.iloc[-1] > close.rolling(10).mean().iloc[-1]
            volume_spike = vol > avg_vol * 1.3

            if momentum and volume_spike:
                candidates.append(symbol)

        except:
            continue

    return candidates
''')

# =========================
# PATCH BOT
# =========================
text = BOT.read_text()

# imports
if "from exit_manager import should_exit" not in text:
    text = text.replace(
        "from rotation_manager import find_weakest_position, should_rotate",
        "from rotation_manager import find_weakest_position, should_rotate\nfrom exit_manager import should_exit\nfrom enhanced_scanner import get_enhanced_candidates"
    )

# patch manage_existing_positions
old_manage = '''def manage_existing_positions():
    positions = get_positions()

    for p in positions:
        symbol = p.symbol
        qty = abs(float(p.qty))
        entry = float(p.avg_entry_price)
        current = float(p.current_price)

        change = (current - entry) / entry

        log(f"P/L | {symbol} | {change:.2%}")

        if change <= -STOP_LOSS_PERCENT:
            sell(symbol, qty, "stop loss")

        elif change >= TAKE_PROFIT_PERCENT:
            sell(symbol, qty, "take profit")

        elif get_trend(symbol) == "bearish":
            sell(symbol, qty, "trend bearish")
'''

new_manage = '''def manage_existing_positions():
    positions = get_positions()

    for p in positions:
        symbol = p.symbol
        qty = abs(float(p.qty))
        entry = float(p.avg_entry_price)
        current = float(p.current_price)

        change = (current - entry) / entry

        log(f"P/L | {symbol} | {change:.2%}")

        if change <= -STOP_LOSS_PERCENT:
            sell(symbol, qty, "stop loss")

        elif change >= TAKE_PROFIT_PERCENT:
            sell(symbol, qty, "take profit")

        elif get_trend(symbol) == "bearish":
            sell(symbol, qty, "trend bearish")

        else:
            exit_now, reason = should_exit(p, get_trend)
            if exit_now:
                sell(symbol, qty, reason)
'''

text = text.replace(old_manage, new_manage)

# patch scanner
text = text.replace(
    "small_caps = get_small_cap_candidates()",
    "small_caps = get_small_cap_candidates()\n        enhanced = get_enhanced_candidates()\n        small_caps = list(set(small_caps + enhanced))"
)

BOT.write_text(text)

print("✅ FULL UPGRADE APPLIED")
print(f"Backup: {backup}")
print("Next:")
print("python3 -m py_compile bot.py exit_manager.py enhanced_scanner.py")
print("sudo systemctl restart tradebot")
