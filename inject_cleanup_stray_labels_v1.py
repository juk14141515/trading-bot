from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_cleanup_labels_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("profit_lab_routes.py")

p = ROOT / "profit_lab_routes.py"
txt = p.read_text()

# Stronger DOM cleanup (kills floating text nodes + stray divs)
if "cleanStrayLabelsV2" not in txt:
    txt = txt.replace(
        "</script>",
        r'''
<script>
function cleanStrayLabelsV2(){
  const bad = ["Losing Exposure", "Risk Level"];

  // Remove loose text nodes
  document.body.childNodes.forEach(n=>{
    if(n.nodeType===3 && bad.includes((n.textContent||"").trim())){
      n.remove();
    }
  });

  // Remove any floating elements outside cards
  document.querySelectorAll("body > div, body > span").forEach(el=>{
    const t = (el.innerText || "").trim();
    if(bad.includes(t)){
      el.remove();
    }
  });
}

cleanStrayLabelsV2();
setInterval(cleanStrayLabelsV2, 3000);
</script>
</script>'''
    )

p.write_text(txt)

print("DONE: stray label cleanup installed")
print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
