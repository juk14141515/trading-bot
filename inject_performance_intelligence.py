from pathlib import Path
from datetime import datetime

FILE = Path("web_dashboard.py")
text = FILE.read_text()

backup = Path(f"web_dashboard_backup_perf_intel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
backup.write_text(text)

logic_marker = "# === PERFORMANCE INTELLIGENCE LOGIC ==="

start = text.find("    return f\"\"\"")
if start == -1:
    raise SystemExit("Could not find dashboard HTML block.")

if logic_marker not in text:
    logic = r'''
    # === PERFORMANCE INTELLIGENCE LOGIC ===
    health_score = 100
    health_notes = []
    health_suggestions = []

    if open_win_rate < 45 and len(positions) > 0:
        health_score -= 20
        health_notes.append("Open win rate is weak.")
        health_suggestions.append("Tighten candidate quality or improve exits before increasing size.")

    if total_pl < 0:
        health_score -= 20
        health_notes.append("Open P/L is negative.")
        health_suggestions.append("Keep rotation defensive and avoid adding weak setups.")

    if scanner_count == 0:
        health_score -= 15
        health_notes.append("Scanner has not produced recent events.")
        health_suggestions.append("Watch scanner logs tomorrow; if still quiet, lower scanner threshold or expand universe.")

    if rotation_count == 0 and status_data.get("slots_available", 0) == 0:
        health_score -= 10
        health_notes.append("No rotations while slots are full.")
        health_suggestions.append("Rotation may need stronger candidate flow before it activates.")

    if adaptive_count == 0:
        health_score -= 5
        health_notes.append("Adaptive learning has not activated yet.")
        health_suggestions.append("Collect more closed trades before enabling factor-level learning.")

    health_score = max(0, min(100, health_score))

    if health_score >= 80:
        health_label = "Strong"
        health_class = "green"
    elif health_score >= 60:
        health_label = "Stable"
        health_class = "yellow"
    else:
        health_label = "Needs Attention"
        health_class = "red"

    if not health_notes:
        health_notes.append("System health looks stable based on current dashboard signals.")

    if not health_suggestions:
        health_suggestions.append("Let the system collect more data before making aggressive changes.")

    health_note_items = ""
    for note in health_notes:
        health_note_items += f"<li>{html.escape(note)}</li>"

    health_suggestion_items = ""
    for suggestion in health_suggestions[:5]:
        health_suggestion_items += f"<li>{html.escape(suggestion)}</li>"
'''
    text = text[:start] + logic + text[start:]

# Recompute after logic injection
start = text.find("    return f\"\"\"")
end = text.find("\n    \"\"\"", start)
if end == -1:
    raise SystemExit("Could not find dashboard HTML end.")

panel = r'''
            <div class="card">
                <h2>Performance Intelligence</h2>
                <div class="grid">
                    <div>
                        <h3>System Health</h3>
                        <div class="big {health_class}">{health_score}/100</div>
                        <p class="muted">{health_label}</p>
                    </div>
                    <div>
                        <h3>Detected Issues</h3>
                        <ul>{health_note_items}</ul>
                    </div>
                    <div>
                        <h3>Suggested Actions</h3>
                        <ul>{health_suggestion_items}</ul>
                    </div>
                </div>
            </div>
'''

insert_before = '            <div class="card">\n                <h2>Position Ranking</h2>'
if insert_before not in text:
    raise SystemExit("Could not find Position Ranking section.")

text = text.replace(insert_before, panel + "\n" + insert_before, 1)

FILE.write_text(text)

print("✅ Performance Intelligence injected")
print(f"✅ Backup created: {backup}")
print("Now run:")
print("python3 -m py_compile web_dashboard.py")
print("sudo systemctl restart tradebot-dashboard")
