from pathlib import Path

p = Path("web_dashboard.py")
text = p.read_text()
p.with_suffix(".py.bak_disable_full_refresh_v1").write_text(text)

text = text.replace('<meta http-equiv="refresh" content="5">', '<!-- full page refresh disabled -->')
text = text.replace('<meta http-equiv="refresh" content="15">', '<!-- history full page refresh disabled -->')

p.write_text(text)
print("✅ Disabled full-page meta refresh")
