from pathlib import Path

FILES = [
    "web_dashboard.py",
    "profit_ops_routes.py",
    "profit_lab_routes.py",
]

SCRIPT = '<script src="/static/ponder_ui.js?v=final"></script>'

for f in FILES:
    p = Path(f)
    if not p.exists():
        print(f"skip {f}")
        continue

    text = p.read_text()
    backup = p.with_suffix(".bak_ui_final")
    backup.write_text(text)

    if "/static/ponder_ui.js" in text:
        print(f"already added in {f}")
        continue

    if "</body>" in text:
        text = text.replace("</body>", SCRIPT + "\n</body>")
    elif "</html>" in text:
        text = text.replace("</html>", SCRIPT + "\n</html>")
    else:
        text += "\n" + SCRIPT

    p.write_text(text)
    print(f"✅ injected into {f}")
