from pathlib import Path

p = Path("web_dashboard.py")
lines = p.read_text().splitlines()

backup = p.with_suffix(".py.bak_ai_health_line_remove")
backup.write_text("\n".join(lines) + "\n")

new_lines = []
removed = 0

for line in lines:
    if "AI Health: {h}/100" in line:
        removed += 1
        continue
    if "Open P/L:" in line and "float(open_pl or 0)" in line:
        removed += 1
        continue
    if "Dashboard</a> · <a href='/profit'" in line:
        removed += 1
        continue

    new_lines.append(line)

p.write_text("\n".join(new_lines) + "\n")
print(f"Removed {removed} bubble lines from web_dashboard.py")
