from pathlib import Path
from datetime import datetime
import re

BOT = Path("bot.py")

text = BOT.read_text()
backup = Path(f"bot_backup_fix_watchlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
backup.write_text(text)

clean_watchlist = '''WATCHLIST = [
    "AAPL", "AMZN", "NVDA", "MSFT", "GOOGL",
    "META", "TSLA", "AMD", "PLTR", "SOFI",
    "COIN", "RBLX", "U",
    "NFLX", "ORCL", "UBER", "SHOP", "PYPL",
    "SQ", "HOOD", "AFRM",
    "NET", "DDOG", "CRWD", "PANW", "ZS",
    "MDB", "APP", "UPST",
    "DKNG", "ROKU",
    "F", "GM", "T", "DIS"
]
'''

pattern = r'WATCHLIST\s*=\s*\[.*?\]\s*\n\nPAPER_ACCOUNT_SIZE'

new_text, count = re.subn(
    pattern,
    clean_watchlist + "\nPAPER_ACCOUNT_SIZE",
    text,
    flags=re.DOTALL,
)

if count == 0:
    raise SystemExit("Could not find WATCHLIST block. bot.py was not changed.")

BOT.write_text(new_text)

print("✅ Watchlist syntax repaired")
print(f"✅ Backup created: {backup}")
print("Now run:")
print("python3 -m py_compile bot.py")
print("sudo systemctl restart tradebot")
