from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

def backup(name):
    p = ROOT / name
    if p.exists():
        b = ROOT / f"{name}.bak_global_app_shell_v1_{STAMP}"
        shutil.copy2(p, b)
        print(f"BACKUP | {name} -> {b.name}")

backup("web_dashboard.py")
backup("profit_lab_routes.py")

# -------------------------
# Global sidebar for pages that do NOT already have it
# -------------------------
p = ROOT / "web_dashboard.py"
txt = p.read_text()

if "GLOBAL_APP_SHELL_V1" not in txt:
    txt += r'''

# GLOBAL_APP_SHELL_V1
@app.after_request
def global_app_shell_v1(response):
    try:
        ctype = response.headers.get("Content-Type", "")
        if "text/html" not in ctype:
            return response

        html = response.get_data(as_text=True)

        # Do not double-inject pages that already have app shell
        if "class=\"sidebar\"" in html or "APP_UI_V1" in html:
            return response

        style = """
<style id="globalAppShellStyle">
:root{--border:#26334f;--green:#7cff9b;--blue:#8ab4ff;--muted:#a8b3c7}
body{background:radial-gradient(circle at top left,#123322 0,#0b1024 35%,#050816 100%)!important}
.globalSidebar{
 position:fixed;left:0;top:0;bottom:0;width:230px;background:rgba(5,10,24,.94);
 border-right:1px solid var(--border);padding:22px 16px;z-index:9999;backdrop-filter:blur(12px);
 font-family:Arial,sans-serif;color:white
}
.globalBrand{font-size:24px;font-weight:900;margin-bottom:24px}
.globalBrand span{color:var(--green)}
.globalNavItem{
 display:block;padding:12px 14px;border-radius:14px;color:#dbe7ff;text-decoration:none;
 margin:8px 0;background:rgba(255,255,255,.03)
}
.globalNavItem:hover{background:rgba(138,180,255,.14);color:white}
.globalSideNote{position:absolute;bottom:20px;color:var(--muted);font-size:12px;line-height:1.4}
body{padding-left:230px!important}
@media(max-width:950px){
 body{padding-left:0!important}
 .globalSidebar{position:static;width:auto;border-right:0;border-bottom:1px solid var(--border)}
 .globalSideNote{position:static;margin-top:12px}
 .globalNavItem{display:inline-block;margin:4px}
}
</style>
"""

        sidebar = """
<div class="globalSidebar">
  <div class="globalBrand">🐾 Ponder<span>AI</span></div>
  <a href="/" class="globalNavItem">🏠 Main</a>
  <a href="/profit" class="globalNavItem">📈 Profit Ops</a>
  <a href="/profit-lab" class="globalNavItem">🧠 Profit Lab</a>
  <a href="/history" class="globalNavItem">📜 History</a>
  <a href="/logout" class="globalNavItem">🔐 Logout</a>
  <div class="globalSideNote">Paper trading dashboard<br>Read-only UI layer</div>
</div>
"""

        html = html.replace("</head>", style + "</head>")
        html = html.replace("<body>", "<body>" + sidebar, 1)

        response.set_data(html)
        response.headers["Content-Length"] = str(len(html.encode("utf-8")))
        return response
    except Exception:
        return response
'''

p.write_text(txt)

# -------------------------
# Clean Profit Lab stray artifact text
# -------------------------
lab = ROOT / "profit_lab_routes.py"
ltxt = lab.read_text()

if "cleanupProfitLabArtifacts" not in ltxt:
    ltxt = ltxt.replace(
        "</script>",
        r'''
<script>
function cleanupProfitLabArtifacts(){
  const bad = ["Losing Exposure", "Risk Level", "--"];
  document.body.childNodes.forEach(n=>{
    if(n.nodeType===3 && bad.includes((n.textContent||"").trim())){
      n.textContent="";
    }
  });
}
cleanupProfitLabArtifacts();
setInterval(cleanupProfitLabArtifacts,3000);
</script>
</script>'''
    )

lab.write_text(ltxt)

print("DONE: Global app shell installed")
print("NEXT:")
print("python3 -m py_compile web_dashboard.py profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
