from pathlib import Path
import re

p = Path("web_dashboard.py")
text = p.read_text()

backup = p.with_suffix(".py.bak_exact_ai_health_bubble")
backup.write_text(text)

pattern = r"""
\s*<div\s+style='font-weight:900'>AI Health:\s*\{h\}/100</div>
\s*<div\s+style='font-size:12px;color:\#a8b3c7'>Open P/L:\s*<span\s+style='color:\{color\}'>\$\{float\(open_pl or 0\):,\.2f\}</span></div>
\s*<div\s+style='font-size:12px;margin-top:6px'><a\s+href='/'\s+style='color:\#8ab4ff'>Dashboard</a>\s*·\s*<a\s+href='/profit'\s+style='color:\#8ab4ff'>Profit Ops</a></div>
"""

text2 = re.sub(pattern, "", text, flags=re.VERBOSE)

if text2 == text:
    print("⚠️ No exact match removed. File unchanged.")
else:
    p.write_text(text2)
    print("✅ Removed exact bottom-right AI Health bubble content from web_dashboard.py")
