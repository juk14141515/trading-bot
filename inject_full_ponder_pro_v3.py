from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

FILES = [
    "web_dashboard.py",
    "profit_ops_routes.py",
    "profit_lab_routes.py",
]

CSS = r'''
/* =========================
   FULL PONDER PRO V3
   UI-only. No trading logic.
========================= */

:root{
  --pp-bg:#050914;
  --pp-card:#101a31;
  --pp-border:#2b3f68;
  --pp-text:#f7f9ff;
  --pp-muted:#aeb9d6;
  --pp-good:#9cffb0;
  --pp-warn:#ffe86b;
  --pp-bad:#ff7896;
  --pp-blue:#8ab4ff;
  --pp-purple:#d7b7ff;
  --pp-radius:24px;
}

body{
  background:
    radial-gradient(circle at 10% 0%, rgba(80,255,170,.12), transparent 30%),
    radial-gradient(circle at 90% 5%, rgba(138,180,255,.12), transparent 34%),
    #050914!important;
  color:var(--pp-text)!important;
  overflow-x:hidden!important;
}

.card,.panel,.metric,.tile,.box{
  border-radius:var(--pp-radius)!important;
  border:1px solid var(--pp-border)!important;
  background:linear-gradient(180deg,rgba(17,26,48,.96),rgba(8,14,28,.96))!important;
  box-shadow:0 20px 55px rgba(0,0,0,.32)!important;
  transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease;
}

.card:hover,.panel:hover,.metric:hover,.tile:hover,.box:hover{
  transform:translateY(-2px);
  border-color:rgba(138,180,255,.7)!important;
  box-shadow:0 26px 70px rgba(0,0,0,.42)!important;
}

.good{color:var(--pp-good)!important}
.bad{color:var(--pp-bad)!important}
.warn{color:var(--pp-warn)!important}
.muted,.label{color:var(--pp-muted)!important}

.pp-command-bar{
  position:fixed;
  top:14px;
  right:18px;
  z-index:9999;
  display:flex;
  align-items:center;
  gap:10px;
  padding:10px 14px;
  border-radius:999px;
  background:rgba(8,14,28,.92);
  border:1px solid var(--pp-border);
  backdrop-filter:blur(16px);
  box-shadow:0 18px 50px rgba(0,0,0,.4);
  font-weight:900;
  color:white;
}

.pp-dot{
  width:10px;
  height:10px;
  border-radius:50%;
  background:var(--pp-good);
  animation:ppPulse 1.6s infinite;
}

@keyframes ppPulse{
  0%{box-shadow:0 0 0 0 rgba(156,255,176,.55)}
  70%{box-shadow:0 0 0 12px rgba(156,255,176,0)}
  100%{box-shadow:0 0 0 0 rgba(156,255,176,0)}
}

.pp-status-chip{
  padding:5px 9px;
  border-radius:999px;
  background:rgba(255,255,255,.07);
  border:1px solid rgba(255,255,255,.1);
  white-space:nowrap;
}

.pp-dock{
  position:fixed;
  right:18px;
  bottom:28px;
  z-index:9999;
  display:flex;
  flex-direction:column;
  gap:10px;
}

.pp-dock button{
  width:46px;
  height:46px;
  border-radius:16px;
  border:1px solid var(--pp-border);
  background:rgba(8,14,28,.92);
  color:white;
  cursor:pointer;
  font-size:18px;
  box-shadow:0 16px 45px rgba(0,0,0,.35);
  backdrop-filter:blur(14px);
}

.pp-dock button:hover{
  transform:translateY(-2px) scale(1.03);
}

.pp-settings{
  position:fixed;
  right:78px;
  bottom:28px;
  width:340px;
  max-width:calc(100vw - 30px);
  z-index:9999;
  display:none;
  padding:18px;
  border-radius:24px;
  border:1px solid var(--pp-border);
  background:rgba(8,14,28,.96);
  backdrop-filter:blur(18px);
  box-shadow:0 28px 80px rgba(0,0,0,.48);
}

.pp-settings.open{
  display:block;
  animation:ppFade .22s ease;
}

@keyframes ppFade{
  from{opacity:0;transform:translateY(8px)}
  to{opacity:1;transform:translateY(0)}
}

.pp-settings h3{
  margin:0 0 12px 0;
}

.pp-setting-row{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:12px;
  padding:10px 0;
  border-top:1px solid rgba(255,255,255,.08);
}

.pp-setting-row label{
  font-weight:900;
}

.pp-setting-row small{
  display:block;
  color:var(--pp-muted);
  font-size:11px;
  margin-top:2px;
}

.pp-toggle{
  min-width:82px;
  border-radius:999px;
  border:1px solid var(--pp-border);
  background:#111b32;
  color:white;
  padding:8px 10px;
  font-weight:900;
  cursor:pointer;
}

.pp-signals{
  margin:18px 0;
  border:1px solid var(--pp-border);
  background:linear-gradient(180deg,rgba(17,26,48,.95),rgba(8,14,28,.95));
  border-radius:24px;
  padding:18px;
  box-shadow:0 20px 55px rgba(0,0,0,.28);
}

.pp-signals h2{
  margin:0 0 12px 0;
}

.pp-signal-grid{
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:12px;
}

.pp-signal{
  padding:12px;
  border-radius:18px;
  border:1px solid rgba(255,255,255,.08);
  background:rgba(255,255,255,.045);
}

.pp-signal .k{
  color:var(--pp-muted);
  font-size:12px;
  font-weight:900;
}

.pp-signal .v{
  margin-top:6px;
  font-size:22px;
  font-weight:1000;
}

.pp-colorblind .good::before{content:"▲ "}
.pp-colorblind .bad::before{content:"▼ "}
.pp-colorblind .warn::before{content:"⚠ "}

.pp-focus table tbody tr:nth-child(n+8){
  display:none;
}

.pp-focus .muted{
  opacity:.82;
}

.pp-highcontrast{
  --pp-bg:#000;
  --pp-card:#07111f;
  --pp-border:#88aaff;
  --pp-text:#fff;
  --pp-muted:#dce6ff;
  --pp-good:#c8ffd7;
  --pp-warn:#fff176;
  --pp-bad:#ff9cb0;
}

.pp-theme-ponder{
  --pp-bg:#070711;
  --pp-card:#151226;
  --pp-border:#5d4a7e;
  --pp-blue:#d7b7ff;
}

.pp-theme-terminal{
  --pp-bg:#020703;
  --pp-card:#07140b;
  --pp-border:#1d7b3a;
  --pp-blue:#72ff9d;
}

.pp-reduced-motion *,
.pp-reduced-motion *::before,
.pp-reduced-motion *::after{
  animation:none!important;
  transition:none!important;
  scroll-behavior:auto!important;
}

#learnTop,#learnStatus,#perfStatus,#perfBest,#perfWorst{
  font-size:clamp(18px,2vw,28px)!important;
  word-break:break-word!important;
  overflow-wrap:anywhere!important;
}

@media(max-width:900px){
  .pp-command-bar{
    top:auto;
    bottom:86px;
    right:12px;
    max-width:calc(100vw - 24px);
    overflow:auto;
  }

  .pp-signal-grid{
    grid-template-columns:1fr;
  }

  .pp-settings{
    right:12px;
    bottom:92px;
  }

  .pp-dock{
    right:12px;
    bottom:150px;
  }
}
'''

JS = r'''
<script id="fullPonderProV3">
(function(){
  if(window.__fullPonderProV3) return;
  window.__fullPonderProV3=true;

  const body=document.body;

  function get(k,d){return localStorage.getItem("pp_"+k) ?? d}
  function set(k,v){localStorage.setItem("pp_"+k,v)}

  function apply(){
    body.classList.toggle("pp-colorblind",get("colorblind","on")==="on");
    body.classList.toggle("pp-focus",get("focus","off")==="on");
    body.classList.toggle("pp-highcontrast",get("contrast","off")==="on");
    body.classList.toggle("pp-reduced-motion",get("motion","on")==="off");

    body.classList.remove("pp-theme-ponder","pp-theme-terminal");
    const theme=get("theme","default");
    if(theme==="ponder") body.classList.add("pp-theme-ponder");
    if(theme==="terminal") body.classList.add("pp-theme-terminal");
  }

  function txt(sel,fallback="--"){
    const el=document.querySelector(sel);
    return el ? el.textContent.trim() : fallback;
  }

  function detectPL(){
    const bodyText=document.body.innerText;
    const match=bodyText.match(/Open P\/L\s*\$?([+\-]?[0-9,.]+)/i) || bodyText.match(/\$[+\-]?[0-9,.]+/);
    return match ? match[0].replace("Open P/L","").trim() : "--";
  }

  function buildBar(){
    if(document.getElementById("ppCommandBar")) return;

    const bar=document.createElement("div");
    bar.id="ppCommandBar";
    bar.className="pp-command-bar";
    bar.innerHTML=`
      <span class="pp-dot"></span>
      <span class="pp-status-chip">LIVE</span>
      <span class="pp-status-chip" id="ppMarket">Market: --</span>
      <span class="pp-status-chip" id="ppHealthMini">Health: --</span>
      <span class="pp-status-chip" id="ppPLMini">P/L: --</span>
    `;
    document.body.appendChild(bar);
  }

  function buildDock(){
    if(document.getElementById("ppDock")) return;

    const dock=document.createElement("div");
    dock.id="ppDock";
    dock.className="pp-dock";
    dock.innerHTML=`
      <button id="ppTop" title="Top">⬆️</button>
      <button id="ppRefresh" title="Refresh">🔄</button>
      <button id="ppCopy" title="Copy status">📋</button>
      <button id="ppSettingsBtn" title="Settings">⚙️</button>
    `;
    document.body.appendChild(dock);

    const settings=document.createElement("div");
    settings.id="ppSettings";
    settings.className="pp-settings";
    settings.innerHTML=`
      <h3>🐾 Ponder Pro Settings</h3>

      <div class="pp-setting-row">
        <div><label>Focus Mode</label><small>Hide extra noise and emphasize key info.</small></div>
        <button class="pp-toggle" data-key="focus">OFF</button>
      </div>

      <div class="pp-setting-row">
        <div><label>Colorblind Mode</label><small>Uses icons/labels, not color alone.</small></div>
        <button class="pp-toggle" data-key="colorblind">ON</button>
      </div>

      <div class="pp-setting-row">
        <div><label>High Contrast</label><small>Sharper text and borders.</small></div>
        <button class="pp-toggle" data-key="contrast">OFF</button>
      </div>

      <div class="pp-setting-row">
        <div><label>Animations</label><small>Toggle smooth motion.</small></div>
        <button class="pp-toggle" data-key="motion">ON</button>
      </div>

      <div class="pp-setting-row">
        <div><label>Theme</label><small>Default / Ponder / Terminal.</small></div>
        <button class="pp-toggle" data-key="theme">DEFAULT</button>
      </div>
    `;
    document.body.appendChild(settings);

    document.getElementById("ppTop").onclick=()=>scrollTo({top:0,behavior:"smooth"});
    document.getElementById("ppRefresh").onclick=()=>{ if(typeof load==="function") load(); else location.reload(); };
    document.getElementById("ppSettingsBtn").onclick=()=>settings.classList.toggle("open");

    document.getElementById("ppCopy").onclick=async()=>{
      const health=document.getElementById("ppHealthMini")?.textContent || "Health unknown";
      const pl=document.getElementById("ppPLMini")?.textContent || "P/L unknown";
      const text=`Ponder Invest AI\n${health}\n${pl}\n${location.href}`;
      try{ await navigator.clipboard.writeText(text); alert("Ponder status copied"); }
      catch(e){ alert(text); }
    };

    settings.querySelectorAll("[data-key]").forEach(btn=>{
      const key=btn.dataset.key;
      function label(){
        let def=key==="colorblind"||key==="motion"?"on":key==="theme"?"default":"off";
        btn.textContent=String(get(key,def)).toUpperCase();
      }
      label();

      btn.onclick=()=>{
        let def=key==="colorblind"||key==="motion"?"on":key==="theme"?"default":"off";
        let v=get(key,def);

        if(key==="theme"){
          v=v==="default"?"ponder":v==="ponder"?"terminal":"default";
        }else{
          v=v==="on"?"off":"on";
        }

        set(key,v);
        label();
        apply();
      };
    });
  }

  function buildSignals(){
    if(document.getElementById("ppSignals")) return;

    const main=document.querySelector("main") || document.querySelector(".content") || document.querySelector(".main") || document.body;
    const h1=document.querySelector("h1");

    const box=document.createElement("div");
    box.id="ppSignals";
    box.className="pp-signals";
    box.innerHTML=`
      <h2>⚡ System Signals</h2>
      <div class="pp-signal-grid">
        <div class="pp-signal"><div class="k">Primary Focus</div><div class="v" id="ppFocusSignal">Monitor</div></div>
        <div class="pp-signal"><div class="k">Risk State</div><div class="v" id="ppRiskSignal">Normal</div></div>
        <div class="pp-signal"><div class="k">Weakest</div><div class="v" id="ppWeakSignal">--</div></div>
        <div class="pp-signal"><div class="k">Next Step</div><div class="v" id="ppNextSignal">Collect Data</div></div>
      </div>
    `;

    if(h1 && h1.parentNode){
      h1.parentNode.insertBefore(box,h1.nextSibling?.nextSibling || h1.nextSibling);
    }else{
      main.prepend(box);
    }
  }

  function updateStatus(){
    const text=document.body.innerText;

    const healthMatch=text.match(/AI Health[:\s]+([0-9.]+\/100)/i) || text.match(/AI Health\s*([0-9.]+\/100)/i);
    const open = /MARKET OPEN|Market:\s*OPEN/i.test(text) ? "OPEN" : (/MARKET CLOSED|Market:\s*CLOSED/i.test(text) ? "CLOSED" : "--");

    const plMatch=text.match(/Open P\/L[\s\S]{0,40}?([+\-]?\$?[0-9,.]+)/i);
    const pl=plMatch ? plMatch[1] : detectPL();

    const weakest=(text.match(/Weakest[:\s]+([A-Z]{1,6})/i)||[])[1] || "--";

    const healthEl=document.getElementById("ppHealthMini");
    const plEl=document.getElementById("ppPLMini");
    const marketEl=document.getElementById("ppMarket");

    if(healthEl) healthEl.textContent="Health: "+(healthMatch?healthMatch[1]:"--");
    if(plEl) plEl.textContent="P/L: "+pl;
    if(marketEl) marketEl.textContent="Market: "+open;

    const risk=document.getElementById("ppRiskSignal");
    const weak=document.getElementById("ppWeakSignal");
    const focus=document.getElementById("ppFocusSignal");
    const next=document.getElementById("ppNextSignal");

    if(risk){
      if(/DO NOT ROTATE|NOT READY/i.test(text)) risk.textContent="Controlled";
      else if(/WATCH|MEDIUM/i.test(text)) risk.textContent="Watch";
      else risk.textContent="Normal";
    }
    if(weak) weak.textContent=weakest;
    if(focus){
      if(/DO NOT ROTATE/i.test(text)) focus.textContent="Hold";
      else if(/WATCH/i.test(text)) focus.textContent="Watch";
      else focus.textContent="Monitor";
    }
    if(next){
      if(/Collecting|not enough closed trades/i.test(text)) next.textContent="Collect Data";
      else next.textContent="Review";
    }
  }

  function fixOldFloating(){
    document.querySelectorAll(".pp-live-pill").forEach(el=>{
      if(el.id!=="ppCommandBar") el.style.display="none";
    });
  }

  function cleanLabels(){
    const learnTop=document.getElementById("learnTop");
    if(learnTop && learnTop.textContent.includes("LEARNING_SHADOW")){
      learnTop.title=learnTop.textContent;
      learnTop.textContent=learnTop.textContent.replace("LEARNING_SHADOW_","").replace("_DECISION","");
    }
  }

  apply();
  buildBar();
  buildDock();
  buildSignals();
  updateStatus();
  fixOldFloating();
  cleanLabels();

  setInterval(()=>{
    updateStatus();
    fixOldFloating();
    cleanLabels();
  },1500);
})();
</script>
'''

for name in FILES:
    path = ROOT / name
    if not path.exists():
        print(f"SKIP | {name} not found")
        continue

    backup = ROOT / f"{name}.bak_full_ponder_pro_v3_{STAMP}"
    shutil.copy2(path, backup)
    print(f"BACKUP | {name} -> {backup.name}")

    txt = path.read_text()
    changed=False

    if "FULL PONDER PRO V3" not in txt:
        if "</style>" in txt:
            txt = txt.replace("</style>", CSS + "\n</style>", 1)
        else:
            txt = CSS + "\n" + txt
        changed=True

    if "fullPonderProV3" not in txt:
        if "</body>" in txt:
            txt = txt.replace("</body>", JS + "\n</body>", 1)
        else:
            txt += "\n" + JS
        changed=True

    if changed:
        path.write_text(txt)
        print(f"DONE | injected {name}")
    else:
        print(f"SKIP | already injected {name}")

print("NEXT:")
print("python3 -m py_compile web_dashboard.py profit_ops_routes.py profit_lab_routes.py")
print("sudo systemctl restart tradebot-dashboard")
