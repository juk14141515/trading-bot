from pathlib import Path
from datetime import datetime

BOT = Path("bot.py")
RISK = Path("risk_manager.py")

bot_text = BOT.read_text()
risk_text = RISK.read_text()

bot_backup = Path(f"bot_backup_trade_frequency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
risk_backup = Path(f"risk_manager_backup_trade_frequency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")

bot_backup.write_text(bot_text)
risk_backup.write_text(risk_text)

# 1) Increase daily trade cap in risk manager
risk_text = risk_text.replace("MAX_TRADES_PER_DAY = 3", "MAX_TRADES_PER_DAY = 5")

# 2) Remove one-buy-per-day lockout safely
old_block = '''    if last_buy_day == today:
        log("SKIP BUY | buy logic already ran today")
        return
'''

new_block = '''    # Buy logic can run multiple times per day.
    # Daily trade count is controlled by risk_manager.py.
'''

if old_block in bot_text:
    bot_text = bot_text.replace(old_block, new_block)
else:
    print("WARNING: one-buy-per-day block not found; no change made there.")

# 3) Add better frequency log
old_today = '''    today = datetime.now().date()
'''

new_today = '''    today = datetime.now().date()
    log("TRADE FREQUENCY | multi-trade mode active | daily cap controlled by risk manager")
'''

if old_today in bot_text:
    bot_text = bot_text.replace(old_today, new_today, 1)

# 4) Slightly improve candidate flow by adding more liquid names to watchlist
extra_symbols = [
    "NFLX", "ORCL", "UBER", "SHOP", "PYPL", "SQ", "HOOD", "AFRM",
    "NET", "DDOG", "CRWD", "PANW", "ZS", "MDB", "APP", "UPST",
    "DKNG", "ROKU", "F", "GM", "T", "DIS"
]

marker = '"SOFI"\n]'
if marker in bot_text:
    added = '", "NFLX", "ORCL", "UBER", "SHOP", "PYPL", "SQ", "HOOD", "AFRM", "NET", "DDOG", "CRWD", "PANW", "ZS", "MDB", "APP", "UPST", "DKNG", "ROKU", "F", "GM", "T", "DIS"\n]'
    bot_text = bot_text.replace(marker, marker.replace("\n]", added), 1)
else:
    print("WARNING: WATCHLIST marker not found; watchlist not expanded.")

BOT.write_text(bot_text)
RISK.write_text(risk_text)

print("✅ Trade frequency patch applied")
print(f"✅ Bot backup: {bot_backup}")
print(f"✅ Risk backup: {risk_backup}")
print("Now run:")
print("python3 -m py_compile bot.py risk_manager.py")
print("sudo systemctl restart tradebot")
