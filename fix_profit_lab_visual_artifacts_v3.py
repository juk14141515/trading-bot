from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

p = ROOT / "profit_lab_routes.py"
backup = ROOT / f"profit_lab_routes.py.bak_visual_artifacts_v3_{STAMP}"
shutil.copy2(p, backup)
print(f"BACKUP | {backup.name}")

txt = p.read_text()

css = """
/* VISUAL_ARTIFACT_CLEANUP_V3 */
.appMain::before,
.appMain::after{
  content:none!important;
}
body{
  overflow-x:hidden!important;
}
"""

js = r"""
<script id="visualArtifactCleanupV3">
function visualArtifactCleanupV3(){
  const bad = new Set(["Losing Exposure","Risk Level","--"]);
  document.querySelectorAll("*").forEach(el=>{
    const text=(el.innerText||"").trim();
    const rect=el.getBoundingClientRect();
    const tiny = rect.width < 180 && rect.height < 80;
    const farLeft = rect.left >= 140 && rect.left < 260;
    const notInCard = !el.closest(".card");
    if(bad.has(text) && tiny && farLeft && notInCard){
      el.style.display="none";
    }
  });
}
setTimeout(visualArtifactCleanupV3, 500);
setInterval(visualArtifactCleanupV3, 3000);
</script>
"""

if "VISUAL_ARTIFACT_CLEANUP_V3" not in txt:
    txt = txt.replace("</style>", css + "\n</style>", 1)

if "visualArtifactCleanupV3" not in txt:
    txt = txt.replace("</body>", js + "\n</body>", 1)

p.write_text(txt)
print("DONE: visual artifact cleanup installed")
