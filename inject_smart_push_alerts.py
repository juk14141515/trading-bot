from pathlib import Path
from datetime import datetime
import re

BOT = Path("bot.py")
PUSH = Path("push_alerts.py")

bot = BOT.read_text()
backup = Path(f"bot_backup_smart_push_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
backup.write_text(bot)

PUSH.write_text(r'''
import os
import subprocess
from pathlib import Path

def _load_env_value(key):
    value = os.getenv(key)
    if value:
        return value

    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return None

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        k, v = line.split("=", 1)
        if k.strip() == key:
            return v.strip().strip('"').strip("'")

    return None


def send_push(title, message, priority="default", tags="chart_with_upwards_trend"):
    topic = _load_env_value("NTFY_TOPIC")

    if not topic:
        print("NTFY_TOPIC missing")
        return False

    url = f"https://ntfy.sh/{topic}"

    try:
        result = subprocess.run(
            [
                "curl",
                "-s",
                "-H", f"Title: {title}",
                "-H", f"Priority: {priority}",
                "-H", f"Tags: {tags}",
                "-d", message,
                url,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        return result.returncode == 0

    except Exception as e:
        print("push error:", e)
        return False


def important_alert(title, message, priority="default", tags="chart_with_upwards_trend"):
    return send_push(title, message, priority, tags)
''')

# Ensure import exists
if "from push_alerts import important_alert" not in bot:
    bot = bot.replace(
        "from metrics_tracker import record_equity_snapshot",
        "from metrics_tracker import record_equity_snapshot\nfrom push_alerts import important_alert"
    )

# Replace notify_discord with smart push + discord
pattern = r'def notify_discord\(message\):\n(.*?)(?=\ndef alert_once|\ndef market_is_open|\ndef )'
match = re.search(pattern, bot, flags=re.DOTALL)

if not match:
    raise SystemExit("Could not find notify_discord function")

new_notify = '''def notify_discord(message):
    url = os.getenv("DISCORD_WEBHOOK_URL")

    try:
        priority = "default"
        tags = "chart_with_upwards_trend"

        upper_msg = str(message).upper()

        if "BOT ERROR" in upper_msg or "STOP_TRADING" in upper_msg or "EMERGENCY" in upper_msg:
            priority = "urgent"
            tags = "rotating_light"
        elif "BUY" in upper_msg:
            priority = "high"
            tags = "moneybag"
        elif "SELL" in upper_msg:
            priority = "high"
            tags = "warning"
        elif "ROTATION" in upper_msg:
            priority = "high"
            tags = "twisted_rightwards_arrows"
        elif "WEAK POSITION" in upper_msg:
            priority = "high"
            tags = "warning"
        elif "SCANNER" in upper_msg:
            priority = "default"
            tags = "mag"

        important_alert("Ponder Invest AI", message, priority, tags)

    except Exception as e:
        try:
            log(f"PUSH | failed | {e}")
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

# Add high-confidence alert after confidence logging
old_conf = '''        log(f"CONFIDENCE | {symbol} | base_score={score} | final_score={final_score}")
'''

new_conf = '''        log(f"CONFIDENCE | {symbol} | base_score={score} | final_score={final_score}")

        if final_score >= 75:
            alert_once(
                f"high_confidence_{symbol}",
                f"🔥 HIGH CONFIDENCE | {symbol} | score={final_score}",
                1800
            )
'''

if old_conf in bot:
    bot = bot.replace(old_conf, new_conf, 1)

# Make scanner alert clearer if patch point exists
old_scan = '''alert_once("scanner_candidates", f"🔎 SCANNER | Enhanced candidates found: {enhanced}", 1800)'''
new_scan = '''alert_once("scanner_candidates", f"🔎 SCANNER | Enhanced candidates found: {enhanced}", 1800)'''

# no-op, kept for compatibility

BOT.write_text(bot)

print("✅ Smart push alerts installed")
print(f"✅ Backup created: {backup}")
print("Now run:")
print("python3 -m py_compile bot.py push_alerts.py")
print("sudo systemctl restart tradebot")
print("")
print("Test:")
print("python3 - <<'PY'")
print("from push_alerts import send_push")
print("from datetime import datetime")
print("print(send_push('Ponder Invest AI', f'Smart push test {datetime.now()}', 'urgent', 'rotating_light'))")
print("PY")
