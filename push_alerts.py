
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
