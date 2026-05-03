from pathlib import Path
import re
import json

ROOT = Path(".")
STATIC = ROOT / "static"
PONDER = STATIC / "ponder"
PONDER.mkdir(parents=True, exist_ok=True)

VERSION = "pondermod2"

(PONDER / "config.json").write_text(json.dumps({
    "version": VERSION,
    "theme": "black_pro",
    "colorblind": True,
    "adhd_mode": False,
    "show_toasts": True,
    "show_ponder": True,
    "refresh_seconds": 60
}, indent=2))

(PONDER / "theme.css").write_text(r'''
:root{
  --ponder-bg:#030712;
  --ponder-panel:#07111f;
  --ponder-card:#0b1220;
  --ponder-border:#334155;
  --ponder-border-strong:#86efac;
  --ponder-text:#f8fafc;
  --ponder-muted:#a8b3c7;
  --ponder-green:#86efac;
  --ponder-yellow:#facc15;
  --ponder-red:#fb7185;
  --ponder-blue:#93c5fd;
  --ponder-radius:20px;
}

#ponderDockV2{
  position:fixed;
  right:22px;
  top:132px;
  z-index:2147483646;
  display:flex;
  flex-direction:column;
  gap:10px;
}

.ponderDockBtn{
  width:52px;
  height:52px;
  border-radius:18px;
  border:1px solid var(--ponder-border);
  background:rgba(7,17,31,.96);
  color:white;
  font-size:24px;
  cursor:pointer;
  box-shadow:0 18px 50px rgba(0,0,0,.45);
}

.ponderDockBtn:hover{
  border-color:var(--ponder-border-strong);
  transform:translateY(-1px);
}

#ponderHubV2Panel{
  position:fixed;
  inset:36px;
  z-index:2147483645;
  overflow:auto;
  background:linear-gradient(180deg,rgba(7,17,31,.98),rgba(2,6,23,.98));
  color:var(--ponder-text);
  border:1px solid var(--ponder-border);
  border-radius:26px;
  box-shadow:0 30px 90px rgba(0,0,0,.72);
  padding:26px;
  font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  display:none;
}

#ponderHubV2Panel *{box-sizing:border-box}

.ponderHeader{
  display:flex;
  justify-content:space-between;
  gap:16px;
  align-items:flex-start;
  margin-bottom:18px;
}

.ponderTitle{
  font-size:34px;
  font-weight:950;
  margin:0;
}

.ponderMuted{
  color:var(--ponder-muted);
  font-size:14px;
}

.ponderClose{
  border:1px solid var(--ponder-border);
  border-radius:14px;
  background:#0f172a;
  color:white;
  padding:10px 14px;
  font-weight:800;
  cursor:pointer;
}

.ponderTabs{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  margin:18px 0;
}

.ponderTab{
  border:1px solid var(--ponder-border);
  background:#0b1220;
  color:#dbeafe;
  border-radius:999px;
  padding:10px 14px;
  cursor:pointer;
  font-weight:850;
}

.ponderTab.active{
  border-color:var(--ponder-green);
  color:white;
  background:rgba(34,197,94,.16);
}

.ponderGrid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
  gap:14px;
  margin:14px 0;
}

.ponderCard{
  border:1px solid var(--ponder-border);
  background:linear-gradient(180deg,rgba(15,23,42,.96),rgba(7,17,31,.96));
  border-radius:var(--ponder-radius);
  padding:18px;
  box-shadow:0 16px 40px rgba(0,0,0,.25);
}

.ponderCard h3{margin:0 0 8px}
.ponderBig{font-size:28px;font-weight:950}
.ponderBadge{
  display:inline-block;
  border:1px solid rgba(134,239,172,.45);
  background:rgba(34,197,94,.12);
  color:#d9fbe3;
  border-radius:999px;
  padding:4px 10px;
  font-weight:850;
  font-size:12px;
}

.ponderTable{
  width:100%;
  border-collapse:collapse;
  margin-top:12px;
  font-size:13px;
}

.ponderTable th,.ponderTable td{
  border-bottom:1px solid rgba(148,163,184,.22);
  padding:10px;
  text-align:left;
  vertical-align:top;
}

.ponderTable th{color:var(--ponder-blue)}

#ponderPupV2{
  position:fixed;
  right:22px;
  bottom:92px;
  width:62px;
  height:62px;
  border-radius:22px;
  border:2px solid var(--ponder-green);
  background:rgba(7,17,31,.98);
  color:white;
  font-size:28px;
  z-index:2147483647;
  cursor:pointer;
  box-shadow:0 20px 60px rgba(0,0,0,.58);
}

#ponderSpeechV2{
  position:fixed;
  right:96px;
  bottom:104px;
  max-width:320px;
  background:rgba(7,17,31,.98);
  border:1px solid rgba(134,239,172,.55);
  color:white;
  border-radius:16px;
  padding:12px 14px;
  font-size:13px;
  line-height:1.35;
  z-index:2147483647;
  box-shadow:0 20px 60px rgba(0,0,0,.55);
  display:none;
}

#ponderToastV2Wrap{
  position:fixed;
  right:22px;
  top:92px;
  z-index:2147483647;
  display:flex;
  flex-direction:column;
  gap:10px;
  max-width:360px;
}

.ponderToastV2{
  background:rgba(7,17,31,.98);
  color:#e5e7eb;
  border:1px solid var(--ponder-border);
  border-radius:16px;
  padding:12px 14px;
  box-shadow:0 18px 55px rgba(0,0,0,.55);
  font-size:13px;
}

.ponderToastV2.critical{border-color:var(--ponder-red)}
.ponderToastV2.warning{border-color:var(--ponder-yellow)}
.ponderToastTitle{font-weight:950;margin-bottom:4px}

.ponderActionBtn{
  border:1px solid var(--ponder-border);
  background:#0f172a;
  color:white;
  border-radius:14px;
  padding:10px 12px;
  cursor:pointer;
  font-weight:850;
  margin:4px;
}

.ponderActionBtn:hover{border-color:var(--ponder-green)}

@media(max-width:850px){
  #ponderHubV2Panel{inset:14px;padding:18px}
  #ponderDockV2{right:12px;top:auto;bottom:172px}
  #ponderPupV2{right:14px;bottom:92px}
  #ponderSpeechV2{right:14px;bottom:164px;max-width:280px}
}
''')

(PONDER / "core.js").write_text(r'''
(function(){
  if(window.PonderV2) return;

  const P = {
    version: "pondermod2",
    isLogin: location.pathname === "/login" || location.pathname.startsWith("/login"),
    async json(path){
      const res = await fetch(path + "?ts=" + Date.now(), {cache:"no-store"});
      if(!res.ok) throw new Error(path + " " + res.status);
      return await res.json();
    },
    safe(v, fallback="—"){
      return (v === undefined || v === null || v === "" || Number.isNaN(v)) ? fallback : v;
    },
    esc(v){
      return String(v ?? "").replace(/[&<>"']/g, c => ({
        "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
      }[c]));
    },
    makeDock(){
      if(this.isLogin) return null;
      let dock = document.getElementById("ponderDockV2");
      if(!dock){
        dock = document.createElement("div");
        dock.id = "ponderDockV2";
        document.body.appendChild(dock);
      }
      return dock;
    },
    addDockButton(id, label, title, handler){
      if(this.isLogin) return;
      const dock = this.makeDock();
      if(!dock || document.getElementById(id)) return;
      const btn = document.createElement("button");
      btn.id = id;
      btn.className = "ponderDockBtn";
      btn.innerHTML = label;
      btn.title = title;
      btn.onclick = handler;
      dock.appendChild(btn);
    },
    say(message, seconds=7){
      if(this.isLogin) return;
      let b = document.getElementById("ponderSpeechV2");
      if(!b){
        b = document.createElement("div");
        b.id = "ponderSpeechV2";
        document.body.appendChild(b);
      }
      b.innerHTML = "🐕 " + this.esc(message);
      b.style.display = "block";
      clearTimeout(window.__ponderSpeechV2Timer);
      window.__ponderSpeechV2Timer = setTimeout(()=> b.style.display="none", seconds*1000);
    },
    copy(text){
      navigator.clipboard?.writeText(text);
      this.say("Snapshot copied. Send it when you need help debugging.");
    }
  };

  window.PonderV2 = P;
  console.log("🐕 Ponder modular core loaded", P.version);
})();
''')

(PONDER / "hub.js").write_text(r'''
(function(){
  const P = window.PonderV2;
  if(!P || P.isLogin || window.__PonderHubV2) return;
  window.__PonderHubV2 = true;

  const files = [
    ["market","/static/research/market_intelligence_latest.json"],
    ["overnight","/static/research/overnight_brief_latest.json"],
    ["sell","/static/research/sell_intelligence_latest.json"],
    ["rotation","/static/research/rotation_engine_latest.json"],
    ["perf","/static/research/rotation_performance_latest.json"],
    ["shadow","/static/research/shadow_capital_allocator_latest.json"],
    ["regime","/static/research/market_regime_filter_latest.json"],
    ["ai","/static/research/ai_summary_latest.json"],
    ["notifications","/static/research/notifications_latest.json"],
    ["assistant","/static/research/ponder_assistant_latest.json"],
    ["achievements","/static/research/achievements_latest.json"]
  ];

  async function loadData(){
    const settled = await Promise.allSettled(files.map(([_,path]) => P.json(path)));
    const d = {};
    files.forEach(([key], i) => d[key] = settled[i].status === "fulfilled" ? settled[i].value : {});
    return d;
  }

  function ensurePanel(){
    let panel = document.getElementById("ponderHubV2Panel");
    if(panel) return panel;
    panel = document.createElement("div");
    panel.id = "ponderHubV2Panel";
    document.body.appendChild(panel);
    return panel;
  }

  const tabs = [
    ["overview","📊 Overview"],
    ["ai","🤖 AI Summary"],
    ["alerts","🔔 Alerts"],
    ["assistant","🐕 Ask Ponder"],
    ["achievements","🎮 Achievements"],
    ["regime","🌡️ Regime"],
    ["rotation","🔄 Rotation"],
    ["performance","📈 Performance"],
    ["debug","🧰 Debug Snapshot"]
  ];

  function tabBar(active){
    return `<div class="ponderTabs">${tabs.map(([id,label]) =>
      `<button class="ponderTab ${active===id?"active":""}" data-ponder-tab="${id}">${label}</button>`
    ).join("")}</div>`;
  }

  function card(title, value, note=""){
    return `<div class="ponderCard"><h3>${title}</h3><div class="ponderBig">${P.safe(value)}</div><div class="ponderMuted">${note}</div></div>`;
  }

  function list(items){
    return `<ul>${(items||[]).map(x=>`<li>${P.esc(x)}</li>`).join("") || "<li>No data yet.</li>"}</ul>`;
  }

  function renderOverview(d){
    const ai = d.ai || {};
    const readout = ai.key_readout || {};
    const n = d.notifications.summary || {};
    return `
      <div class="ponderGrid">
        ${card("Regime", readout.regime || d.regime.regime, "Score: " + P.safe(readout.regime_score || d.regime.regime_score))}
        ${card("News Impact", readout.news_impact || d.regime.news_impact || 0, "Higher = more caution")}
        ${card("Top Rotation", (readout.top_rotation||{}).move || "None", (readout.top_rotation||{}).action || "")}
        ${card("Alerts", n.total || 0, `${n.critical||0} critical · ${n.warning||0} warnings`)}
      </div>
      <h2>🧭 What Should I Do?</h2>
      <div class="ponderCard" style="border-color:var(--ponder-green)">${list(ai.action_items)}</div>
      <h2>Plain-English Summary</h2>
      <div class="ponderCard">${list(ai.plain_english_summary)}</div>
    `;
  }

  function renderAi(d){
    const ai = d.ai || {};
    const readout = ai.key_readout || {};
    const news = ai.top_news || [];
    return `
      <div class="ponderGrid">
        ${card("Regime", readout.regime, "Score: " + P.safe(readout.regime_score))}
        ${card("Top Rotation", (readout.top_rotation||{}).move, `${(readout.top_rotation||{}).action || ""} · ${(readout.top_rotation||{}).confidence || ""}`)}
        ${card("Learning", readout.pending_evaluations, "Pending evaluations")}
      </div>
      <h2>🧭 What Should I Do Right Now?</h2>
      <div class="ponderCard" style="border-color:var(--ponder-green)">${list(ai.action_items)}</div>
      <h2>Summary</h2>
      <div class="ponderCard">${list(ai.plain_english_summary)}</div>
      <h2>Top News Drivers</h2>
      <table class="ponderTable"><thead><tr><th>Headline</th><th>Source</th><th>Impact</th><th>Tags</th></tr></thead><tbody>
      ${news.map(n=>`<tr><td><strong>${P.esc(n.headline)}</strong></td><td>${P.esc(n.source)}</td><td>${P.safe(n.impact_score)}</td><td>${(n.tags||[]).join(", ")}</td></tr>`).join("") || `<tr><td colspan="4">No news drivers.</td></tr>`}
      </tbody></table>
    `;
  }

  function renderAlerts(d){
    const n = d.notifications || {};
    const s = n.summary || {};
    const alerts = n.alerts || [];
    return `
      <div class="ponderGrid">
        ${card("Critical", s.critical || 0)}
        ${card("Warnings", s.warning || 0)}
        ${card("Achievements", s.achievement || 0)}
        ${card("Total", s.total || alerts.length || 0)}
      </div>
      <table class="ponderTable"><thead><tr><th>Level</th><th>Category</th><th>Title</th><th>Message</th></tr></thead><tbody>
      ${alerts.map(a=>`<tr><td><span class="ponderBadge">${P.esc(a.level)}</span></td><td>${P.esc(a.category)}</td><td><strong>${P.esc(a.title)}</strong></td><td>${P.esc(a.message)}</td></tr>`).join("") || `<tr><td colspan="4">No alerts.</td></tr>`}
      </tbody></table>
    `;
  }

  function renderAssistant(d){
    const a = d.assistant || {};
    const ans = a.answers || {};
    const buttons = [
      ["why_no_trade","Why didn’t you trade?"],
      ["biggest_risk","What is the biggest risk?"],
      ["should_rotate","Should I rotate?"],
      ["what_to_do","What should I do?"],
      ["plain_english","Explain simply"]
    ];
    return `
      <div class="ponderGrid">
        ${card("Mode", (a.overseer||{}).market_regime, "Ponder watches risk first.")}
        ${card("News Impact", (a.overseer||{}).news_impact)}
        ${card("Learning", ((a.overseer||{}).learning||{}).pending, "Pending outcomes")}
      </div>
      <div class="ponderCard">
        ${buttons.map(([k,label])=>`<button class="ponderActionBtn" data-answer="${k}">${label}</button>`).join("")}
      </div>
      <div class="ponderCard" id="ponderAnswerV2">Click a question and Ponder will answer using current research data.</div>
      <script>
        setTimeout(()=>{
          const answers = ${JSON.stringify(ans).replace(/</g,"\\u003c")};
          document.querySelectorAll("[data-answer]").forEach(btn=>{
            btn.onclick = ()=>{
              const key = btn.dataset.answer;
              const box = document.getElementById("ponderAnswerV2");
              const items = answers[key] || [];
              box.innerHTML = "<ul>" + items.map(x=>"<li>"+x+"</li>").join("") + "</ul>";
              window.PonderV2?.say("I answered using the latest research data.");
            };
          });
        },50);
      </script>
    `;
  }

  function renderAchievements(d){
    const a = d.achievements || {};
    const rows = a.achievements || [];
    return `
      <div class="ponderGrid">
        ${card("Unlocked", a.total_unlocked || rows.length || 0, "Game layer")}
        ${card("Next Goal", "More data", "Let the bot collect outcomes")}
      </div>
      <div class="ponderGrid">
      ${rows.map(x=>`<div class="ponderCard"><h3>${P.esc(x.title)}</h3><p>${P.esc(x.description)}</p></div>`).join("") || `<div class="ponderCard">No achievements yet.</div>`}
      </div>
    `;
  }

  function renderRegime(d){
    const r = d.regime || {};
    return `<div class="ponderGrid">
      ${card("Regime", r.regime)}
      ${card("Score", r.regime_score)}
      ${card("News Impact", r.news_impact || 0)}
    </div><div class="ponderCard">${list(r.reasons)}</div>`;
  }

  function renderRotation(d){
    const rows = d.rotation.rotation_suggestions || [];
    return `<table class="ponderTable"><thead><tr><th>Move</th><th>Action</th><th>Score</th><th>Regime</th></tr></thead><tbody>
      ${rows.slice(0,30).map(x=>`<tr><td><strong>${P.esc(x.sell_symbol)} → ${P.esc(x.buy_symbol)}</strong></td><td>${P.esc(x.action)}</td><td>${P.safe(x.rotation_score)}</td><td>${P.esc(x.regime||"")}</td></tr>`).join("") || `<tr><td colspan="4">No rotations.</td></tr>`}
    </tbody></table>`;
  }

  function renderPerformance(d){
    const s = d.perf.summary || {};
    const h = d.perf.by_horizon || {};
    return `<div class="ponderGrid">
      ${card("Win Rate", (s.win_rate || 0) + "%", s.primary_horizon || "60m")}
      ${card("Evaluated", s.evaluated || 0)}
      ${card("Pending", s.pending_evaluations || 0)}
      ${card("Avg Alpha", (s.avg_alpha_pct || 0) + "%")}
    </div><pre class="ponderCard">${P.esc(JSON.stringify(h,null,2))}</pre>`;
  }

  function renderDebug(d){
    const snapshot = {
      time:new Date().toISOString(),
      url:location.href,
      version:P.version,
      ai:d.ai?.key_readout,
      alerts:d.notifications?.summary,
      regime:d.regime,
      rotation:d.rotation?.top_rotation,
      perf:d.perf?.summary
    };
    const text = JSON.stringify(snapshot,null,2);
    return `<div class="ponderCard"><button class="ponderActionBtn" id="copySnapshotV2">Copy Debug Snapshot</button><pre>${P.esc(text)}</pre></div>
      <script>setTimeout(()=>{document.getElementById("copySnapshotV2").onclick=()=>window.PonderV2.copy(${JSON.stringify(text)});},50)</script>`;
  }

  const renderers = {overview:renderOverview, ai:renderAi, alerts:renderAlerts, assistant:renderAssistant, achievements:renderAchievements, regime:renderRegime, rotation:renderRotation, performance:renderPerformance, debug:renderDebug};

  async function openHub(tab="overview"){
    const panel = ensurePanel();
    panel.style.display = "block";
    panel.innerHTML = `<div class="ponderHeader"><div><h1 class="ponderTitle">🐾 PonderAI Command Center</h1><div class="ponderMuted">Modular research-only dashboard layer.</div></div><button class="ponderClose" id="ponderCloseV2">Close</button></div><p class="ponderMuted">Loading...</p>`;
    const d = await loadData();
    const active = renderers[tab] ? tab : "overview";
    panel.innerHTML = `<div class="ponderHeader"><div><h1 class="ponderTitle">🐾 PonderAI Command Center</h1><div class="ponderMuted">Research-only. No live orders from this UI.</div></div><button class="ponderClose" id="ponderCloseV2">Close</button></div>${tabBar(active)}<div>${renderers[active](d)}</div>`;
    document.getElementById("ponderCloseV2").onclick = ()=> panel.style.display = "none";
    panel.querySelectorAll("[data-ponder-tab]").forEach(b => b.onclick = ()=> openHub(b.dataset.ponderTab));
  }

  window.PonderV2.openHub = openHub;
  P.addDockButton("ponderHubV2Button","🧠","PonderAI Command Center",()=>openHub("overview"));
})();
''')

(PONDER / "alerts.js").write_text(r'''
(function(){
  const P = window.PonderV2;
  if(!P || P.isLogin || window.__PonderAlertsV2) return;
  window.__PonderAlertsV2 = true;

  function wrap(){
    let w = document.getElementById("ponderToastV2Wrap");
    if(!w){
      w = document.createElement("div");
      w.id = "ponderToastV2Wrap";
      document.body.appendChild(w);
    }
    return w;
  }

  function toast(a){
    const key = "ponder_v2_seen_" + (a.key || (a.level + "::" + a.title + "::" + a.message));
    if(localStorage.getItem(key)) return;
    localStorage.setItem(key,"1");

    const el = document.createElement("div");
    el.className = "ponderToastV2 " + (a.level || "info");
    el.innerHTML = `<div class="ponderToastTitle">🐕 ${P.esc(a.title || "Ponder Alert")}</div><div>${P.esc(a.message || "")}</div>`;
    wrap().appendChild(el);
    setTimeout(()=>el.remove(), a.level === "critical" ? 10000 : 7000);
  }

  async function poll(){
    try{
      const data = await P.json("/static/research/notifications_latest.json");
      (data.alerts || []).filter(a=>["critical","warning"].includes(a.level)).slice(0,3).forEach(toast);
    }catch(e){}
  }

  setTimeout(poll, 1800);
  setTimeout(poll, 6000);
  setInterval(poll, 60000);
})();
''')

(PONDER / "assistant.js").write_text(r'''
(function(){
  const P = window.PonderV2;
  if(!P || P.isLogin || window.__PonderAssistantDogV2) return;
  window.__PonderAssistantDogV2 = true;

  function button(){
    let b = document.getElementById("ponderPupV2");
    if(b) return b;
    b = document.createElement("button");
    b.id = "ponderPupV2";
    b.innerHTML = "🐕";
    b.title = "Ask Ponder";
    b.onclick = ()=> P.openHub ? P.openHub("assistant") : P.say("Open the command center first.");
    document.body.appendChild(b);
    return b;
  }

  function mood(summary={}){
    if((summary.critical||0)>0) return ["🛡️🐕","Guard Mode","#fb7185","Ponder is guarding you. Critical risk is active."];
    if((summary.warning||0)>0) return ["⚠️🐕","Alert Mode","#facc15","Ponder smells risk. Stay careful."];
    if((summary.total||0)===0) return ["😴🐕","Idle Mode","#94a3b8","Ponder is resting. No major alerts."];
    return ["🐕","Watch Mode","#86efac","Ponder is watching the system."];
  }

  async function update(){
    const b = button();
    try{
      const data = await P.json("/static/research/notifications_latest.json");
      const [icon,title,border,msg] = mood(data.summary || {});
      b.innerHTML = icon;
      b.title = title;
      b.style.borderColor = border;
      if(b.dataset.mode !== title){
        b.dataset.mode = title;
        P.say(msg);
      }
    }catch(e){}
  }

  setTimeout(update, 1200);
  setInterval(update, 45000);
})();
''')

(PONDER / "achievements.js").write_text(r'''
(function(){
  const P = window.PonderV2;
  if(!P || P.isLogin || window.__PonderAchievementsV2) return;
  window.__PonderAchievementsV2 = true;
  // Reserved for future XP progress popups. Achievements render inside hub.
})();
''')

# Patch web_dashboard.py
wd = Path("web_dashboard.py")
text = wd.read_text()
backup = Path("web_dashboard.py.bak_modular_ui_v2_patch")
backup.write_text(text)

# Remove old ponder_ui script tags
text = re.sub(r'\n?\s*<script src="/static/ponder_ui\.js\?v=[^"]+"></script>', '', text)

# Add request import if needed
if "from flask import" in text and "request" not in text.split("from flask import",1)[1].split("\n",1)[0]:
    text = text.replace("from flask import ", "from flask import request, ", 1)

loader = f'''
# === PONDER_MODULAR_UI_V2 ===
@app.after_request
def ponder_modular_ui_v2(response):
    try:
        if request.path.startswith("/login"):
            return response
        ctype = response.headers.get("Content-Type", "")
        if "text/html" not in ctype:
            return response
        html = response.get_data(as_text=True)
        if "/static/ponder/core.js" in html:
            return response
        assets = """
<link rel="stylesheet" href="/static/ponder/theme.css?v={VERSION}">
<script src="/static/ponder/core.js?v={VERSION}"></script>
<script src="/static/ponder/hub.js?v={VERSION}"></script>
<script src="/static/ponder/alerts.js?v={VERSION}"></script>
<script src="/static/ponder/assistant.js?v={VERSION}"></script>
<script src="/static/ponder/achievements.js?v={VERSION}"></script>
"""
        if "</body>" in html:
            html = html.replace("</body>", assets + "\\n</body>")
        else:
            html += assets
        response.set_data(html)
    except Exception:
        pass
    return response
# === END_PONDER_MODULAR_UI_V2 ===
'''

if "PONDER_MODULAR_UI_V2" not in text:
    marker = 'if __name__ == "__main__":'
    if marker in text:
        text = text.replace(marker, loader + "\n" + marker)
    else:
        text += "\n" + loader

wd.write_text(text)
print("✅ Installed modular Ponder UI v2")
print("✅ Files written under static/ponder/")
print("✅ Backup:", backup)
