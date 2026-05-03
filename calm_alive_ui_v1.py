from pathlib import Path
import re

p = Path("static/ponder_ui.js")
text = p.read_text()
p.with_suffix(".js.bak_calm_alive_v1").write_text(text)

# Disable broad pulse classes/animations
text = text.replace("animation: ponderPulse 2.4s ease-in-out infinite;", "animation: none;")

# Disable the function that scans every div/span and adds pulse
text = re.sub(
    r"\n\s*function pulseLive\(\) \{.*?\n\s*\}\n",
    "\n  function pulseLive() { return; }\n",
    text,
    flags=re.S
)

p.write_text(text)
print("✅ Calmed UI breathing animation")
