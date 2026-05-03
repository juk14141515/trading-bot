import re

FILE = "bot.py"

with open(FILE, "r") as f:
    lines = f.readlines()

new_lines = []
inside_fix_block = False

for line in lines:
    # Detect the broken if block (over-indented)
    if re.match(r"\s+if not market_is_open\(\):", line):
        inside_fix_block = True

        new_lines.append("    if not market_is_open():\n")
        new_lines.append("        log(\"Market closed\")\n\n")
        new_lines.append("        update_status({\n")
        new_lines.append("            \"market_trend\": \"closed\",\n")
        new_lines.append("            \"watchlist\": [],\n")
        new_lines.append("            \"top_candidates\": [],\n")
        new_lines.append("            \"positions\": len(get_positions()),\n")
        new_lines.append("            \"slots_available\": 0,\n")
        new_lines.append("            \"summary\": {\n")
        new_lines.append("                \"market_summary\": \"Market is currently closed.\",\n")
        new_lines.append("                \"opportunity_summary\": \"No trading opportunities while market is closed.\",\n")
        new_lines.append("                \"risk_summary\": \"No new trade risk while bot is idle.\",\n")
        new_lines.append("                \"watchlist_summary\": \"Scanner will resume when the market opens.\",\n")
        new_lines.append("                \"full_summary\": \"Market closed. Bot is online, idle, and waiting for the next trading session.\"\n")
        new_lines.append("            }\n")
        new_lines.append("        })\n\n")
        new_lines.append("        return\n")

        continue

    # Skip old broken block until we exit it
    if inside_fix_block:
        if "return" in line:
            inside_fix_block = False
        continue

    new_lines.append(line)

# Backup
with open(FILE + ".backup_fix", "w") as f:
    f.writelines(lines)

# Write fixed file
with open(FILE, "w") as f:
    f.writelines(new_lines)

print("✅ Fixed market closed indentation + backed up original")
