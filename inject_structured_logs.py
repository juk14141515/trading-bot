from pathlib import Path
from datetime import datetime

BOT = Path("bot.py")

backup = Path(f"bot_backup_structured_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
text = BOT.read_text()
backup.write_text(text)

replacements = {
    'log("No buys | SPY not bullish")':
    'log("SKIP BUY | SPY not bullish")',

    'log("No buys | max positions reached")':
    'log("SKIP BUY | max positions reached")',

    'log("Buy logic skipped | already ran today")':
    'log("SKIP BUY | buy logic already ran today")',

    'log("Trading halted for today")':
    'log("SKIP BUY | trading halted for today")',

    'log("Market closed")':
    'log("SKIP BUY | market closed")',
}

changed = 0
for old, new in replacements.items():
    if old in text:
        text = text.replace(old, new)
        changed += 1

# Add stronger decision log before buy if missing
old_buy_decision = 'log(f"BUY DECISION | {symbol} | score={final_score}")'
new_buy_decision = 'log(f"BUY DECISION | {symbol} | score={final_score} | reason=qualified candidate passed risk checks")'

if old_buy_decision in text:
    text = text.replace(old_buy_decision, new_buy_decision)
    changed += 1

# Improve final buy log if present
old_buy_log = 'log(f"BUY | {symbol} | ${dollars} | score={score}")'
new_buy_log = 'log(f"BUY | {symbol} | dollars={dollars:.2f} | score={score} | reason=order submitted")'

if old_buy_log in text:
    text = text.replace(old_buy_log, new_buy_log)
    changed += 1

# Improve sell log
old_sell_log = 'log(f"SELL | {symbol} | {reason}")'
new_sell_log = 'log(f"SELL | {symbol} | reason={reason}")'

if old_sell_log in text:
    text = text.replace(old_sell_log, new_sell_log)
    changed += 1

# Improve rotation approved log if present
old_rotation = 'log(f"ROTATION APPROVED | sell={weakest_position[\'symbol\']} | buy={symbol} | score={final_score} | reason={rotate_reason}")'
new_rotation = 'log(f"ROTATION APPROVED | replacing={weakest_position[\'symbol\']} | new={symbol} | score={final_score} | reason={rotate_reason}")'

if old_rotation in text:
    text = text.replace(old_rotation, new_rotation)
    changed += 1

# Improve no rotation log
old_no_rotation = 'log(f"NO ROTATION | {symbol} | {rotate_reason}")'
new_no_rotation = 'log(f"NO ROTATION | candidate={symbol} | reason={rotate_reason}")'

if old_no_rotation in text:
    text = text.replace(old_no_rotation, new_no_rotation)
    changed += 1

BOT.write_text(text)

print("✅ Structured logging patch applied")
print(f"✅ Backup created: {backup}")
print(f"✅ Replacements made: {changed}")
print("Now run:")
print("python3 -m py_compile bot.py")
print("sudo systemctl restart tradebot")
