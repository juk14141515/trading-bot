from pathlib import Path
from datetime import datetime
import re

BOT = Path("bot.py")
bot = BOT.read_text()

backup = Path(f"bot_backup_push_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
backup.write_text(bot)

Path("push_alerts.py").write_text(r'''
import os
import json
import urllib.request
from datetime import datetime

def send_push(title, message, priority="default"):
    topic = os.getenv("NTFY_TOPIC")

    if not topic:
        return False

    url = f"https://ntfy.sh/{topic}"

    data = message.encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Title": title,
            "Priority": priority,
            "Tags": "chart_with_upwards_trend"
        }
    )

    try:
        urllib.request.urlopen(req, timeout=5)
        return True
    except Exception:
        return False


def important_alert(title, message, priority="default"):
    send_push(title, message, priority)
''')

# import push alerts
if "from push_alerts import important_alert" not in bot:
    bot = bot.replace(
        "from metrics_tracker import record_equity_snapshot",
        "from metrics_tracker import record_equity_snapshot\nfrom push_alerts import important_alert"
    )

# upgrade notify_discord to also send push
pattern = r'def notify_discord\(message\):\n(.*?)(?=\ndef alert_once|\ndef market_is_open|\ndef )'
match = re.search(pattern, bot, flags=re.DOTALL)

if not match:
    raise SystemExit("Could not find notify_discord function.")

new_notify = '''def notify_discord(message):
    url = os.getenv("DISCORD_WEBHOOK_URL")

    try:
        important_alert("Ponder Invest AI", message)
    except Exception:
        pass

    if not url:
        log("DISCORD | missing webhook url")
        return

    try:
        requests.post(url, json={"content": message}, timeout=5)
    except Exception as e:
        log(f"DISCORD | failed | {e}")

'''

bot = bot[:match.start()] + new_notify + bot[match.end():]

# add market closed daily summary alert once
if "alert_once(\"market_closed_status\"" not in bot:
    bot = bot.replace(
        'log("SKIP BUY | market closed")',
        'log("SKIP BUY | market closed")\n        alert_once("market_closed_status", "📴 Ponder Invest AI | Market closed | bot online and waiting", 21600)',
        1
    )

# add dashboard-style important stop alert if missing
if "STOP_TRADING active" in bot and "important_alert(\"Ponder Invest AI Stop\"" not in bot:
    bot = bot.replace(
        'notify_discord("🚨 STOP_TRADING active | bot will not place new trades")',
        'notify_discord("🚨 STOP_TRADING active | bot will not place new trades")\n        important_alert("Ponder Invest AI Stop", "STOP_TRADING is active. Bot will not place trades.", "urgent")'
    )

BOT.write_text(bot)

print("✅ Push alerts installed")
print(f"✅ Backup created: {backup}")
print("Now run:")
print("python3 -m py_compile bot.py push_alerts.py")
print("sudo systemctl restart tradebot")
