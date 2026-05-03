from pathlib import Path

service_path = Path("/etc/systemd/system/tradebot-dashboard.service")

if not service_path.exists():
    print("❌ Service file not found:", service_path)
    raise SystemExit

text = service_path.read_text()
backup = service_path.with_suffix(".service.bak_env_fix_v1")
backup.write_text(text)

if "EnvironmentFile=" in text:
    print("⚠️ EnvironmentFile already exists, skipping insert")
else:
    lines = text.splitlines()
    new_lines = []
    inserted = False

    for line in lines:
        new_lines.append(line)

        if line.strip() == "[Service]" and not inserted:
            new_lines.append("EnvironmentFile=/home/ubuntu/trading-bot/.env")
            inserted = True

    text = "\n".join(new_lines) + "\n"
    service_path.write_text(text)
    print("✅ Injected EnvironmentFile into service")

print(f"Backup saved: {backup}")
