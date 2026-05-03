import re
import shutil
from datetime import datetime

BOT_FILE = "bot.py"

backup = f"bot.py.backup_scanloop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy(BOT_FILE, backup)
print(f"Backup created: {backup}")

with open(BOT_FILE, "r") as f:
    content = f.read()

# Ensure import exists
import_line = "from small_cap_scanner import get_small_cap_candidates\n"
if import_line not in content:
    content = content.replace(
        "from risk_manager import can_trade\n",
        "from risk_manager import can_trade\n" + import_line
    )

new_block_template = '''{i}candidates = []

{i}try:
{i}    small_caps = get_small_cap_candidates()
{i}except Exception as e:
{i}    log(f"Small-cap scanner error: {{e}}")
{i}    small_caps = []

{i}dynamic_watchlist = list(dict.fromkeys(WATCHLIST + small_caps))
{i}log(f"Dynamic watchlist: {{dynamic_watchlist}}")

{i}for symbol in dynamic_watchlist:
{i}    if symbol == "SPY":
{i}        continue

{i}    if already_holding(symbol):
{i}        continue

{i}    trend = get_trend(symbol)
{i}    analyst = finnhub_analyst_score(symbol)
{i}    news = news_score(symbol)

{i}    trend_score = 100 if trend == "bullish" else 0

{i}    total = calculate_weighted_score(
{i}        trend_score=trend_score,
{i}        analyst_score=analyst * 10,
{i}        news_score=max(0, min(100, news * 10)),
{i}        momentum_score=get_momentum_score(symbol),
{i}        volatility_score=50,
{i}    )

{i}    log(f"{{symbol}} | trend={{trend}} | analyst={{analyst}} | news={{news}} | total={{total}}")

{i}    if trend == "bullish" and analyst >= 3 and news >= 0:
{i}        candidates.append((symbol, total))

{i}candidates.sort(key=lambda x: x[1], reverse=True)

{i}for symbol, score in candidates[:slots_available]:
{i}    final_score = score

{i}    allowed, reason = can_trade(symbol, final_score)
{i}    if not allowed:
{i}        log(f"SKIP BUY | {{symbol}} | {{reason}}")
{i}        notify_discord(f"⏩ SKIP BUY | {{symbol}} | {{reason}}")
{i}        continue

{i}    log(f"BUY DECISION | {{symbol}} | score={{final_score}}")
{i}    buy(symbol, final_score)

{i}last_buy_day = today'''

pattern = re.compile(
    r'(?ms)^([ \t]*)candidates = \[\].*?^\1last_buy_day = today'
)

match = pattern.search(content)
if not match:
    print("ERROR: Could not find scan loop block.")
    print("Backup was created, no changes made.")
    raise SystemExit(1)

indent = match.group(1)
new_block = new_block_template.format(i=indent)

content = pattern.sub(new_block, content, count=1)

with open(BOT_FILE, "w") as f:
    f.write(content)

print("Scan loop replaced successfully.")
