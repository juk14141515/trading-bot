import shutil

FILE = "web_dashboard.py"

# Backup
backup = FILE + ".backup_render_fix"
shutil.copy(FILE, backup)
print(f"Backup created: {backup}")

with open(FILE, "r") as f:
    lines = f.readlines()

new_lines = []
skip = False

for i, line in enumerate(lines):

    # REMOVE broken duplicate AI block
    if "<!-- AI SUMMARY BLOCK -->" in line:
        skip = True
        continue

    if skip:
        if "</div>" in line and "grid" not in line:
            skip = False
        continue

    new_lines.append(line)

# NOW insert AI summary in correct place (after top cards)
output = []
inserted = False

for i, line in enumerate(new_lines):
    output.append(line)

    # insert AFTER buying power section ends
    if "</div>" in line and "Buying Power" in "".join(new_lines[max(0,i-5):i]):
        if not inserted:
            output.append("""
            <!-- AI SUMMARY -->
            {ai_summary_html}
            """)
            inserted = True

with open(FILE, "w") as f:
    f.writelines(output)

print("✅ Dashboard render fixed")
