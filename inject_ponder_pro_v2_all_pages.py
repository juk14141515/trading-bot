from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

FILES = [
    "profit_lab_routes.py",
    "profit_ops_routes.py",
    "web_dashboard.py",
]

CSS = r'''
/* =========================
   PONDER PRO V2 ALL PAGES
   UI-only. No trading logic.
========================= */

/* Move live badge below nav so it does not cover page links */
.pp-live-pill{
  top:86px!important;
  right:22px!important;
}

/* Better spacing for top right nav/links */
nav, .nav, .topnav, .links{
  padding-right:180px!important;
}

/* App polish */
body{
  overflow-x:hidden!important;
}

.card, .panel, .metric, .box, .tile{
  position:relative;
  overflow:hidden;
}

.card::after, .panel::after, .metric::after, .box::after, .tile::after{
  content:"";
  position:absolute;
  inset:0;
  pointer-events:none;
  border-radius:inherit;
  background:linear-gradient(135deg,rgba(255,255,255,.045),transparent 35%);
  opacity:.55;
}

/* Fix giant overflow text in learning/event panels */
#learnTop,
#learnStatus,
#perfStatus,
#perfBest,
#perfWorst{
  font-size:clamp(18px,2vw,28px)!important;
  line-height:1.15!important;
  word-break:break-word!important;
  overflow-wrap:anywhere!important;
  max-width:100%!important;
}

/* Tables become app-like */
table{
  width:100%;
  border-collapse:collapse;
}

tr{
  transition:background .18s ease, transform .18s ease;
}

tbody tr:hover{
  background:rgba(138,180,255,.08)!important;
}

/* Better scrollbar */
::-webkit-scrollbar{
  width:10px;
  height:10px;
}
::-webkit-scrollbar-track{
  background:#050914;
}
::-webkit-scrollbar-thumb{
  background:#2a3f69;
  border-radius:999px;
}
::-webkit-scrollbar-thumb:hover{
  background:#45629e;
}

/* Floating app tool dock */
.pp-tool-dock{
  position:fixed;
  right:22px;
  top:136px;
  z-index:9998;
  display:flex;
  flex-direction:column;
  gap:10px;
}

.pp-mini-btn{
  border:1px solid var(--pp-border,#263a63);
  background:rgba(12,20,38,.9);
  color:white;
  border-radius:14px;
  width:42px;
  height:42px;
  cursor:pointer;
  box-shadow:0 14px 35px rgba(0,0,0,.32);
  backdrop-filter:blur(12px);
}

.pp-mini-btn:hover{
  transform:translateY(-2px) scale(1.03);
}

/* Cleaner mobile */
@media(max-width:900px){
  .pp-live-pill{
    top:auto!important;
    bottom:88px!important;
    right:14px!important;
  }

  .pp-tool-dock{
    top:auto!important;
    right:14px!important;
    bottom:150px!important;
  }

  nav, .nav, .topnav, .links{
    padding-right:0!important;
  }

  .card, .panel, .metric, .box, .tile{
    border-radius:18px!important;
  }
}

/* Focus mode: hide secondary clutter more safely */
.pp-focus .muted{
  opacity:.82;
}

.pp-focus table tbody tr:nth-child(n+8){
  display:none;
}

/* Colorblind mode stronger labels */
.pp-colorblind .good,
.pp-colorblind .bad,
.pp-colorblind .warn{
  font-weight:900!important;
}
'''

JS = r'''
<script id="ponderProV2">
(function(){
  if(window.__ponderProV2Loaded) return;
  window.__ponderProV2Loaded = true;

  function qs(s){return document.querySelector(s)}
  function qsa(s){return Array.from(document.querySelectorAll(s))}

  function toast(msg){
    let t=document.getElementById("ppToast");
    if(!t){
      t=document.createElement("div");
      t.id="ppToast";
      t.style.cssText="position:fixed;left:50%;bottom:34px;transform:translateX(-50%);z-index:10000;background:rgba(10,16,31,.95);border:1px solid var(--pp-border,#263a63);color:white;padding:12px 16px;border-radius:999px;font-weight:900;box-shadow:0 18px 45px rgba(0,0,0,.35);display:none";
      document.body.appendChild(t);
    }
    t.textContent=msg;
    t.style.display="block";
    clearTimeout(window.__ppToastTimer);
    window.__ppToastTimer=setTimeout(()=>t.style.display="none",1600);
  }

  function makeDock(){
    if(document.getElementById("ppToolDock")) return;
    const dock=document.createElement("div");
    dock.id="ppToolDock";
    dock.className="pp-tool-dock";
    dock.innerHTML=`
      <button class="pp-mini-btn" title="Top" id="ppGoTop">⬆️</button>
      <button class="pp-mini-btn" title="Refresh" id="ppDockRefresh">🔄</button>
      <button class="pp-mini-btn" title="Copy status" id="ppCopyStatus">📋</button>
    `;
    document.body.appendChild(dock);

    document.getElementById("ppGoTop").onclick=()=>window.scrollTo({top:0,behavior:"smooth"});

    document.getElementById("ppDockRefresh").onclick=()=>{
      if(typeof load==="function"){ load(); toast("Ponder refreshed"); }
      else { location.reload(); }
    };

    document.getElementById("ppCopyStatus").onclick=async()=>{
      const health=(document.body.innerText.match(/AI Health[:\s]+[0-9.]+\/100/i)||["AI Health unknown"])[0];
      const pl=(document.body.innerText.match(/Open P\/L[:\s$+\-.0-9,]+/i)||["Open P/L unknown"])[0];
      const text=`Ponder Invest AI Status\n${health}\n${pl}\nPage: ${location.pathname}`;
      try{
        await navigator.clipboard.writeText(text);
        toast("Status copied");
      }catch(e){
        toast("Copy unavailable");
      }
    };
  }

  function fixLiveBadge(){
    const pill=document.getElementById("ppLivePill") || document.querySelector(".pp-live-pill");
    if(pill){
      pill.style.top="86px";
      pill.style.right="22px";
    }
  }

  function cleanLearningLabels(){
    const top=document.getElementById("learnTop");
    if(top && top.textContent.length > 22){
      top.title=top.textContent;
      top.textContent=top.textContent.replace("LEARNING_SHADOW_","").replace("_DECISION","");
    }
  }

  function enhanceLinks(){
    qsa("a").forEach(a=>{
      if(!a.dataset.ppSmooth){
        a.dataset.ppSmooth="1";
        a.addEventListener("click",()=>document.body.style.opacity=".94");
      }
    });
  }

  makeDock();
  fixLiveBadge();
  cleanLearningLabels();
  enhanceLinks();

  setInterval(()=>{
    fixLiveBadge();
    cleanLearningLabels();
    enhanceLinks();
  },1500);
})();
</script>
'''

for name in FILES:
    path = ROOT / name
    if not path.exists():
        print(f"SKIP | {name} not found")
        continue

    backup = ROOT / f"{name}.bak_ponder_pro_v2_{STAMP}"
    shutil.copy2(path, backup)
    print(f"BACKUP | {name} -> {backup.name}")

    txt = path.read_text()
    changed = False

    if "PONDER PRO V2 ALL PAGES" not in txt:
        if "</style>" in txt:
            txt = txt.replace("</style>", CSS + "\n</style>", 1)
        else:
            txt = CSS + "\n" + txt
        changed = True

    if "ponderProV2" not in txt:
        if "</body>" in txt:
            txt = txt.replace("</body>", JS + "\n</body>", 1)
        else:
            txt += "\n" + JS
        changed = True

    if changed:
        path.write_text(txt)
        print(f"DONE | injected {name}")
    else:
        print(f"SKIP | already injected {name}")

print("NEXT:")
print("python3 -m py_compile profit_lab_routes.py profit_ops_routes.py web_dashboard.py")
print("sudo systemctl restart tradebot-dashboard")
