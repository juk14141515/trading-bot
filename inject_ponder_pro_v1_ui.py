from pathlib import Path
from datetime import datetime
import shutil

ROOT = Path("/home/ubuntu/trading-bot")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

TARGETS = [
    "profit_lab_routes.py",
    "profit_ops_routes.py",
    "web_dashboard.py",
]

CSS = r'''
/* =========================
   PONDER PRO V1 UI SYSTEM
   UI-only. No trading logic.
========================= */
:root{
  --pp-bg:#050914;
  --pp-panel:#111a30;
  --pp-panel2:#0d1528;
  --pp-border:#263a63;
  --pp-text:#f4f7ff;
  --pp-muted:#aab6d3;
  --pp-accent:#8ab4ff;
  --pp-good:#7dff9b;
  --pp-warn:#ffe66d;
  --pp-bad:#ff6b8a;
  --pp-radius:22px;
  --pp-speed:220ms;
}

html{scroll-behavior:smooth}
body{
  background:
    radial-gradient(circle at top left, rgba(51,255,153,.12), transparent 32%),
    radial-gradient(circle at top right, rgba(138,180,255,.10), transparent 30%),
    var(--pp-bg)!important;
  color:var(--pp-text)!important;
  transition:background var(--pp-speed), color var(--pp-speed);
}

.card, .panel, .metric, .box, .tile{
  border-radius:var(--pp-radius)!important;
  border:1px solid var(--pp-border)!important;
  background:linear-gradient(180deg, rgba(17,26,48,.96), rgba(10,16,31,.96))!important;
  box-shadow:0 18px 45px rgba(0,0,0,.28)!important;
  transition:transform var(--pp-speed), border-color var(--pp-speed), box-shadow var(--pp-speed);
}

.card:hover, .panel:hover, .metric:hover, .box:hover, .tile:hover{
  transform:translateY(-2px);
  border-color:rgba(138,180,255,.65)!important;
  box-shadow:0 22px 55px rgba(0,0,0,.36)!important;
}

.value{
  letter-spacing:.02em;
  transition:color var(--pp-speed), transform var(--pp-speed);
}

.good{color:var(--pp-good)!important}
.bad{color:var(--pp-bad)!important}
.warn{color:var(--pp-warn)!important}
.muted,.label{color:var(--pp-muted)!important}

a, button{
  transition:transform var(--pp-speed), opacity var(--pp-speed), background var(--pp-speed), border-color var(--pp-speed);
}
button:hover, a:hover{transform:translateY(-1px)}

.pp-live-pill{
  position:fixed;
  top:14px;
  right:18px;
  z-index:9999;
  display:flex;
  align-items:center;
  gap:8px;
  padding:10px 14px;
  border-radius:999px;
  background:rgba(12,20,38,.88);
  border:1px solid var(--pp-border);
  backdrop-filter:blur(14px);
  font-weight:900;
  color:var(--pp-text);
  box-shadow:0 16px 40px rgba(0,0,0,.35);
}

.pp-dot{
  width:10px;
  height:10px;
  border-radius:50%;
  background:var(--pp-good);
  box-shadow:0 0 0 0 rgba(125,255,155,.65);
  animation:ppPulse 1.8s infinite;
}

@keyframes ppPulse{
  0%{box-shadow:0 0 0 0 rgba(125,255,155,.55)}
  70%{box-shadow:0 0 0 12px rgba(125,255,155,0)}
  100%{box-shadow:0 0 0 0 rgba(125,255,155,0)}
}

.pp-settings{
  position:fixed;
  right:18px;
  bottom:92px;
  z-index:9999;
  width:320px;
  max-width:calc(100vw - 30px);
  border-radius:22px;
  border:1px solid var(--pp-border);
  background:rgba(8,14,28,.95);
  backdrop-filter:blur(18px);
  box-shadow:0 24px 65px rgba(0,0,0,.42);
  padding:16px;
  display:none;
}

.pp-settings.open{display:block; animation:ppFadeIn .22s ease}
@keyframes ppFadeIn{from{opacity:0; transform:translateY(8px)} to{opacity:1; transform:translateY(0)}}

.pp-settings h3{
  margin:0 0 10px 0;
  font-size:18px;
}

.pp-row{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:12px;
  padding:9px 0;
  border-top:1px solid rgba(255,255,255,.07);
}

.pp-row label{font-weight:800;color:var(--pp-text)}
.pp-row small{display:block;color:var(--pp-muted);font-size:11px;margin-top:2px}

.pp-toggle{
  cursor:pointer;
  border:1px solid var(--pp-border);
  border-radius:999px;
  padding:7px 10px;
  background:#101a31;
  color:var(--pp-text);
  font-weight:900;
  min-width:72px;
}

.pp-gear{
  position:fixed;
  right:18px;
  bottom:34px;
  z-index:9999;
  border:1px solid var(--pp-border);
  background:linear-gradient(180deg,#172542,#10182d);
  color:white;
  border-radius:999px;
  width:48px;
  height:48px;
  font-size:22px;
  box-shadow:0 18px 45px rgba(0,0,0,.38);
  cursor:pointer;
}

.pp-focus .muted,
.pp-focus table,
.pp-focus .decisionReplay,
.pp-focus #decisionReplay{
  font-size:.92em;
}

.pp-focus .card:not(:has(#rotScore)):not(:has(#ponderQuestion)):not(:has(#perfStatus)):not(:has(#positions)){
  opacity:.82;
}

.pp-colorblind .good::before{content:"▲ "; color:currentColor}
.pp-colorblind .bad::before{content:"▼ "; color:currentColor}
.pp-colorblind .warn::before{content:"⚠ "; color:currentColor}

.pp-highcontrast{
  --pp-bg:#000;
  --pp-panel:#07111f;
  --pp-panel2:#020817;
  --pp-border:#7aa2ff;
  --pp-text:#ffffff;
  --pp-muted:#d7e1ff;
  --pp-accent:#ffffff;
  --pp-good:#b7ffce;
  --pp-warn:#fff176;
  --pp-bad:#ff9cb0;
}

.pp-theme-ponder{
  --pp-bg:#070711;
  --pp-panel:#151226;
  --pp-panel2:#100e1d;
  --pp-border:#5d4a7e;
  --pp-accent:#d9b8ff;
  --pp-good:#9cffb5;
  --pp-warn:#ffe082;
  --pp-bad:#ff7fa3;
}

.pp-theme-terminal{
  --pp-bg:#020703;
  --pp-panel:#07140b;
  --pp-panel2:#051007;
  --pp-border:#1d7b3a;
  --pp-accent:#72ff9d;
  --pp-good:#72ff9d;
  --pp-warn:#fff176;
  --pp-bad:#ff6b6b;
}

.pp-reduced-motion *,
.pp-reduced-motion *::before,
.pp-reduced-motion *::after{
  animation:none!important;
  transition:none!important;
  scroll-behavior:auto!important;
}

@media(max-width:800px){
  .pp-live-pill{top:auto;bottom:88px;right:14px;font-size:12px}
  .pp-settings{right:12px;bottom:86px}
}
'''

JS = r'''
<script id="ponderProV1">
(function(){
  if(window.__ponderProV1Loaded) return;
  window.__ponderProV1Loaded = true;

  const root = document.documentElement;
  const body = document.body;

  function get(k,d){return localStorage.getItem("ponderPro_"+k) ?? d}
  function set(k,v){localStorage.setItem("ponderPro_"+k,v)}

  function apply(){
    body.classList.toggle("pp-focus", get("focus","off")==="on");
    body.classList.toggle("pp-colorblind", get("colorblind","on")==="on");
    body.classList.toggle("pp-highcontrast", get("contrast","off")==="on");
    body.classList.toggle("pp-reduced-motion", get("motion","on")==="off");

    body.classList.remove("pp-theme-ponder","pp-theme-terminal");
    const theme=get("theme","default");
    if(theme==="ponder") body.classList.add("pp-theme-ponder");
    if(theme==="terminal") body.classList.add("pp-theme-terminal");

    const accent=get("accent","");
    if(accent) root.style.setProperty("--pp-accent", accent);
  }

  function makeUI(){
    if(document.getElementById("ppLivePill")) return;

    const live=document.createElement("div");
    live.id="ppLivePill";
    live.className="pp-live-pill";
    live.innerHTML='<span class="pp-dot"></span><span id="ppLiveText">LIVE · Ponder Pro</span>';
    document.body.appendChild(live);

    const gear=document.createElement("button");
    gear.className="pp-gear";
    gear.innerHTML="⚙️";
    gear.title="Ponder Pro settings";
    gear.onclick=()=>document.getElementById("ppSettings").classList.toggle("open");
    document.body.appendChild(gear);

    const panel=document.createElement("div");
    panel.id="ppSettings";
    panel.className="pp-settings";
    panel.innerHTML=`
      <h3>🐾 Ponder Pro Settings</h3>

      <div class="pp-row">
        <div><label>Focus Mode</label><small>Reduce noise and emphasize key panels.</small></div>
        <button class="pp-toggle" data-key="focus">OFF</button>
      </div>

      <div class="pp-row">
        <div><label>Colorblind Mode</label><small>Uses labels/icons, not color alone.</small></div>
        <button class="pp-toggle" data-key="colorblind">ON</button>
      </div>

      <div class="pp-row">
        <div><label>High Contrast</label><small>Sharper borders and readable text.</small></div>
        <button class="pp-toggle" data-key="contrast">OFF</button>
      </div>

      <div class="pp-row">
        <div><label>Animations</label><small>Smooth app feel or reduced motion.</small></div>
        <button class="pp-toggle" data-key="motion">ON</button>
      </div>

      <div class="pp-row">
        <div><label>Theme</label><small>Default / Ponder / Terminal.</small></div>
        <button class="pp-toggle" data-key="theme">DEFAULT</button>
      </div>

      <div class="pp-row">
        <div><label>Refresh</label><small>Refresh page data manually.</small></div>
        <button class="pp-toggle" id="ppRefreshNow">NOW</button>
      </div>
    `;
    document.body.appendChild(panel);

    panel.querySelectorAll("[data-key]").forEach(btn=>{
      const key=btn.dataset.key;
      function label(){
        let v=get(key, key==="colorblind"||key==="motion" ? "on" : key==="theme" ? "default" : "off");
        btn.textContent=String(v).toUpperCase();
      }
      label();

      btn.onclick=()=>{
        let v=get(key, key==="colorblind"||key==="motion" ? "on" : key==="theme" ? "default" : "off");

        if(key==="theme"){
          v = v==="default" ? "ponder" : v==="ponder" ? "terminal" : "default";
        }else{
          v = v==="on" ? "off" : "on";
        }

        set(key,v);
        label();
        apply();
      };
    });

    document.getElementById("ppRefreshNow").onclick=()=>{
      const text=document.getElementById("ppLiveText");
      text.textContent="Refreshing...";
      if(typeof load==="function"){ load(); }
      setTimeout(()=>text.textContent="LIVE · Ponder Pro",900);
    };
  }

  function enhance(){
    const title = document.querySelector("h1");
    if(title && !title.dataset.pp){
      title.dataset.pp="1";
      title.innerHTML = title.innerHTML.replace("Ponder", "🐾 Ponder");
    }

    document.querySelectorAll(".value").forEach(el=>{
      if(!el.dataset.ppWatch){
        el.dataset.ppWatch=el.textContent;
      }else if(el.dataset.ppWatch !== el.textContent){
        el.animate([{transform:"scale(1.02)",filter:"brightness(1.4)"},{transform:"scale(1)",filter:"brightness(1)"}],{duration:260});
        el.dataset.ppWatch=el.textContent;
      }
    });
  }

  apply();
  makeUI();
  enhance();
  setInterval(enhance,1500);
})();
</script>
'''

for name in TARGETS:
    path = ROOT / name
    if not path.exists():
        print(f"SKIP | {name} not found")
        continue

    backup = ROOT / f"{name}.bak_ponder_pro_v1_{STAMP}"
    shutil.copy2(path, backup)
    print(f"BACKUP | {name} -> {backup.name}")

    txt = path.read_text()

    changed = False

    if "PONDER PRO V1 UI SYSTEM" not in txt:
        if "</style>" in txt:
            txt = txt.replace("</style>", CSS + "\n</style>", 1)
        else:
            txt = CSS + "\n" + txt
        changed = True

    if "ponderProV1" not in txt:
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
