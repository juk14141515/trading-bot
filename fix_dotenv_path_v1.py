from pathlib import Path

files = [
    Path("overnight_brief_v1.py"),
]

for p in files:
    if not p.exists():
        print(f"⚠️ Missing: {p}")
        continue

    text = p.read_text()
    backup = p.with_suffix(p.suffix + ".bak_dotenv_path")
    backup.write_text(text)

    text = text.replace("load_dotenv()", 'load_dotenv(dotenv_path=".env")')

    p.write_text(text)
    print(f"✅ Fixed dotenv path in {p}")
    print(f"Backup saved: {backup}")
