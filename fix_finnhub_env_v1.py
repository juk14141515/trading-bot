from pathlib import Path

p = Path("overnight_brief_v1.py")
text = p.read_text()

backup = Path("overnight_brief_v1.py.bak_load_dotenv")
backup.write_text(text)

if "from dotenv import load_dotenv" not in text:
    text = text.replace(
        "import os\n",
        "import os\nfrom dotenv import load_dotenv\n"
    )

if "load_dotenv()" not in text:
    marker = "from pathlib import Path\n"
    text = text.replace(
        marker,
        marker + "\nload_dotenv()\n"
    )

p.write_text(text)
print("✅ Patched overnight_brief_v1.py to load .env")
print(f"Backup saved: {backup}")
