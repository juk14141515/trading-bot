from pathlib import Path

FILES = [
    "web_dashboard.py",
    "profit_ops_routes.py",
    "profit_lab_routes.py",
]

SCRIPT = '<script src="/static/ponder_ui.js?v=ponderui1"></script>'

for name in FILES:
    p = Path(name)
    if not p.exists():
        print(f"skip missing {name}")
        continue

    text = p.read_text()
    backup = p.with_suffix(p.suffix + ".bak_ponder_ui_loader_v1")
    backup.write_text(text)

    if "/static/ponder_ui.js" in text:
        print(f"already linked {name}")
        continue

    if "</body>" in text:
        text = text.replace("</body>", SCRIPT + "\n</body>", 1)
    elif "</html>" in text:
        text = text.replace("</html>", SCRIPT + "\n</html>", 1)
    else:
        text += "\n" + SCRIPT + "\n"

    p.write_text(text)
    print(f"✅ linked ponder_ui.js in {name}")
