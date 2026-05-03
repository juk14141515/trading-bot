from pathlib import Path
import re, json

ROOT = Path(".")
APP = ROOT / "static" / "ponder4"
APP.mkdir(parents=True, exist_ok=True)

VERSION = "ponder4_v1"

(APP / "settings.json").write_text(json.dumps({
    "version": VERSION,
    "theme": "midnight",
    "accent": "blue",
    "colorblind": True,
    "reduced_motion": True,
    "compact": False,
    "refresh_seconds": 45
}, indent=2))

(APP / "theme.css").write_text(r'''
:root{
  --p4-bg:#020617;
  --p4-panel:#07111f;
  --p4-card:#0b1220;
  --p4-border:#263349;
  --p4-text:#f8fafc;
  --p4-muted:#a8b3c7;
  --p4-accent:#93c5fd;
  --p4-good:#86efac;
  --p4-warn:#facc15;
  --p4-risk:#fb7185;
  --p4-radius:18px;
}
body{background:#020617!important}
#ponderV3Sidebar,#ponderV3Main,#ponderV3Pup,#ponderV3Speech,#ponderV3ToastWrap,
#ponderDockV2,#ponderHubV2Panel,#ponderPupV2,#ponderSpeechV2,#ponderToastV2Wrap,
#ponderHubBtn,#ponderIntelBtn,#ponderLearningBtn,#ponderPupBtn,#ponderDogAssistantBtn{
  display:none!important;visibility:hidden!important;pointer-events:none!important;
}
#p4Shell{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--p4-text)}
#p4Top{
  position:fixed;left:0;right:0;top:0;height:58px;z-index:2147482500;
  background:rgba(2,6,23,.92);backdrop-filter:blur(10px);
  border-bottom:1px solid var(--p4-border);display:flex;align-items:center;gap:12px;padding:0 18px;
}
#p4Brand{font-size:21px;font-weight:950;min-width:190px}
#p4Brand span{color:var(--p4-accent)}
.p4Nav{display:flex;gap:8px;flex-wrap:wrap}
.p4Nav a,.p4Btn{
  color:#dbeafe;text-decoration:none;border:1px solid var(--p4-border);
  background:#0b1220;border-radius:999px;padding:9px 12px;font-weight:800;font-size:13px;cursor:pointer;
}
.p4Nav a:hover,.p4Btn:hover{border-color:var(--p4-accent)}
#p4Status{margin-left:auto;color:var(--p4-muted);font-size:12px}
body{padding-top:58px!important}
#p4AssistantBtn{
  position:fixed;right:24px;bottom:96px;width:62px;height:62px;border-radius:22px;
  background:#07111f;border:2px solid var(--p4-accent);z-index:2147483600;
  color:white;font-size:27px;cursor:pointer;box-shadow:0 18px 55px rgba(0,0,0,.55);
}
#p4AssistantPanel,#p4ResearchPanel{
  position:fixed;z-index:2147483550;background:linear-gradient(180deg,#07111f,#020617);
  border:1px solid var(--p4-border);box-shadow:0 30px 90px rgba(0,0,0,.7);
  color:var(--p4-text);font-family:system-ui,-apple-system,"Segoe UI",sans-serif;
}
#p4AssistantPanel{
  right:24px;bottom:172px;width:420px;max-width:calc(100vw - 36px);
  border-radius:22px;display:none;overflow:hidden;
}
#p4ResearchPanel{
  left:28px;right:28px;top:82px;bottom:28px;border-radius:24px;display:none;overflow:hidden;
}
.p4Head{display:flex;align-items:center;justify-content:space-between;padding:16px 18px;border-bottom:1px solid var(--p4-border)}
.p4Title{font-size:22px;font-weight:950}
.p4Body{padding:18px;overflow:auto;max-height:calc(100vh - 160px)}
#p4ResearchPanel .p4Body{height:calc(100% - 64px);max-height:none}
.p4Grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:14px 0}
.p4Card{background:linear-gradient(180deg,#0b1220,#07111f);border:1px solid var(--p4-border);border-radius:18px;padding:16px}
.p4Card h3{margin:0 0 8px;font-size:14px;color:#bfdbfe}
.p4Big{font-size:27px;font-weight:950}
.p4Muted{color:var(--p4-muted);font-size:13px}
.p4Tabs{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}
.p4Tab{border:1px solid var(--p4-border);background:#0b1220;color:white;border-radius:999px;padding:9px 12px;font-weight:850;cursor:pointer}
.p4Tab.active{border-color:var(--p4-accent);background:rgba(147,197,253,.12)}
.p4Table{width:100%;border-collapse:collapse;font-size:13px}
.p4Table th,.p4Table td{border-bottom:1px solid rgba(148,163,184,.22);padding:10px;text-align:left;vertical-align:top}
.p4Badge{display:inline-block;border:1px solid var(--p4-border);border-radius:999px;padding:4px 9px;font-weight:850;font-size:12px}
.p4Risk{border-color:var(--p4-risk);color:#fecdd3}.p4Warn{border-color:var(--p4-warn);color:#fef3c7}.p4Good{border-color:var(--p4-good);color:#dcfce7}
.p4Q{width:100%;text-align:left;margin:6px 0;border:1px solid var(--p4-border);background:#0b1220;color:white;border-radius:14px;padding:11px 12px;font-weight:850;cursor:pointer}
#p4Answer{margin-top:10px}
#p4ToastWrap{position:fixed;right:24px;top:74px;z-index:2147483650;display:flex;flex-direction:column;gap:10px;max-width:370px}
.p4Toast{background:#07111f;border:1px solid var(--p4-border);border-radius:15px;padding:12px;color:white;box-shadow:0 18px 55px rgba(0,0,0,.55)}
.p4Toast.critical{border-color:var(--p4-risk)}.p4Toast.warning{border-color:var(--p4-warn)}
.p4SettingsRow{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid rgba(148,163,184,.18);padding:12px 0}
@media(max-width:800px){
  #p4Top{height:auto;min-height:58px;align-items:flex-start;padding:10px;flex-direction:column}
  body{padding-top:128px!important}
  #p4ResearchPanel{left:10px;right:10px;top:138px;bottom:10px}
}
''')

(APP / "app.js").write_text(r'''
(function(){
  if(window.__PonderSiteV4) return;
  window.__PonderSiteV4 = true;
  if(location.pathname.startsWith("/login")) return;

  const P = {
    data:{},
    sources:{
      market:"/static/research/market_intelligence_latest.json",
      overnight:"/static/research/overnight_brief_latest.json",
      sell:"/static/research/sell_intelligence_latest.json",
      rotation:"/static/research/rotation_engine_latest.json",
      perf:"/static/research/rotation_performance_latest.json",
      shadow:"/static/research/shadow_capital_allocator_latest.json",
      regime:"/static/research/market_regime_filter_latest.json",
      ai:"/static/research/ai_summary_latest.json",
      alerts:"/static/research/notifications_latest.json",
      assistant:"/static/research/ponder_assistant_latest.json",
      achievements:"/static/research/achievements_latest.json"
    },
    safe(v,f="—"){return (v===undefined||v===null||v===""||Number.isNaN(v))?f:v},
    esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))},
    async json(path){const r=await fetch(path+"?ts="+Date.now(),{cache:"no-store"}); if(!r.ok) throw new Error(path); return await r.json()},
    async load(){
      const e=Object.entries(this.sources);
      const s=await Promise.allSettled(e.map(([_,p])=>this.json(p)));
      e.forEach(([k],i)=>this.data[k]=s[i].status==="fulfilled"?s[i].value:{});
      return this.data;
    },
    copy(text){navigator.clipboard?.writeText(text); this.toast({level:"info",title:"Copied",message:"Debug snapshot copied."})},
    toast(a){
      const key="p4_seen_"+(a.level+"::"+a.title+"::"+a.message);
      if(localStorage.getItem(key)) return;
      localStorage.setItem(key,"1");
      let w=document.getElementById("p4ToastWrap");
      if(!w){w=document.createElement("div");w.id="p4ToastWrap";document.body.appendChild(w)}
      const el=document.createElement("div"); el.className="p4Toast "+(a.level||"");
      el.innerHTML=`<b>🐕 ${this.esc(a.title)}</b><br>${this.esc(a.message)}`;
      w.appendChild(el); setTimeout(()=>el.remove(),a.level==="critical"?10000:7000);
    }
  };
  window.PonderSiteV4=P;

  function card(t,v,n=""){return `<div class="p4Card"><h3>${t}</h3><div class="p4Big">${P.safe(v)}</div><div class="p4Muted">${n}</div></div>`}
  function list(xs){return `<ul>${(xs||[]).map(x=>`<li>${P.esc(x)}</li>`).join("")||"<li>No data yet.</li>"}</ul>`}

  function shell(){
    if(document.getElementById("p4Shell")) return;
    const div=document.createElement("div"); div.id="p4Shell";
    div.innerHTML=`
      <div id="p4Top">
        <div id="p4Brand">🐾 Ponder<span>AI</span></div>
        <nav class="p4Nav">
          <a href="/">Main</a><a href="/profit">Profit Ops</a><a href="/profit-lab">Profit Lab</a><a href="/history">History</a>
          <button class="p4Btn" id="p4ResearchBtn">Research Center</button>
          <button class="p4Btn" id="p4SettingsBtn">Settings</button>
        </nav>
        <div id="p4Status">research-only</div>
      </div>
      <button id="p4AssistantBtn" title="Ask Ponder">🐕</button>
      <section id="p4AssistantPanel"></section>
      <section id="p4ResearchPanel"></section>
    `;
    document.body.appendChild(div);
    document.getElementById("p4AssistantBtn").onclick=()=>assistant();
    document.getElementById("p4ResearchBtn").onclick=()=>research("overview");
    document.getElementById("p4SettingsBtn").onclick=()=>research("settings");
  }

  function assistantAnswer(key){
    const d=P.data, ai=d.ai||{}, a=d.assistant||{}, ans=a.answers||{};
    let out=ans[key]||[];
    if(!out.length && key==="why") out=[
      `Current regime is ${P.safe(d.regime?.regime)} with news impact ${P.safe(d.regime?.news_impact||ai.key_readout?.news_impact)}.`,
      `Top rotation is ${(ai.key_readout?.top_rotation||{}).move||"not clear"} but confidence/action is not strong enough.`,
      `Ponder recommends staying research-only until more outcomes are evaluated.`
    ];
    if(!out.length && key==="do") out=ai.action_items||["Review AI Summary and Alerts first."];
    if(!out.length && key==="risk") out=[`Biggest current risk appears to be ${P.safe(d.regime?.regime)} / news impact ${P.safe(d.regime?.news_impact)}.`];
    if(!out.length && key==="changed") out=["Use Debug Snapshot now and compare it with a prior snapshot. Deeper change tracking is planned."];
    return `<ul>${out.map(x=>`<li>${P.esc(x)}</li>`).join("")}</ul>`;
  }

  async function assistant(){
    await P.load();
    const p=document.getElementById("p4AssistantPanel");
    p.style.display=p.style.display==="block"?"none":"block";
    p.innerHTML=`
      <div class="p4Head"><div class="p4Title">🐕 Ask Ponder</div><button class="p4Btn" id="p4CloseAssistant">Close</button></div>
      <div class="p4Body">
        <div class="p4Grid">
          ${card("Mode",P.safe(P.data.regime?.regime),"assistant/overseer")}
          ${card("News Impact",P.safe(P.data.regime?.news_impact||P.data.ai?.key_readout?.news_impact))}
        </div>
        <button class="p4Q" data-q="why">Why didn’t you trade?</button>
        <button class="p4Q" data-q="do">What should I do now?</button>
        <button class="p4Q" data-q="risk">Where is the risk?</button>
        <button class="p4Q" data-q="changed">What changed since last time?</button>
        <div id="p4Answer" class="p4Card">Click a question.</div>
      </div>`;
    document.getElementById("p4CloseAssistant").onclick=()=>p.style.display="none";
    p.querySelectorAll("[data-q]").forEach(b=>b.onclick=()=>document.getElementById("p4Answer").innerHTML=assistantAnswer(b.dataset.q));
  }

  const tabs=["overview","ai","alerts","market","overnight","sell","rotation","shadow","performance","learning","future","settings","debug"];
  function tabbar(active){return `<div class="p4Tabs">${tabs.map(t=>`<button class="p4Tab ${t===active?"active":""}" data-tab="${t}">${label(t)}</button>`).join("")}</div>`}
  function label(t){return ({overview:"Overview",ai:"AI Summary",alerts:"Alerts",market:"Market",overnight:"Overnight",sell:"Sell",rotation:"Rotation",shadow:"Shadow",performance:"Performance",learning:"Learning",future:"Future Labs",settings:"Settings",debug:"Debug"})[t]||t}

  async function research(tab="overview"){
    await P.load();
    const p=document.getElementById("p4ResearchPanel"); p.style.display="block";
    p.innerHTML=`<div class="p4Head"><div><div class="p4Title">PonderAI Research Center</div><div class="p4Muted">research-only · ${new Date().toLocaleTimeString()}</div></div><button class="p4Btn" id="p4CloseResearch">Close</button></div><div class="p4Body">${tabbar(tab)}${render(tab)}</div>`;
    document.getElementById("p4CloseResearch").onclick=()=>p.style.display="none";
    p.querySelectorAll("[data-tab]").forEach(b=>b.onclick=()=>research(b.dataset.tab));
    bindInside(tab);
  }

  function render(tab){
    const d=P.data, ai=d.ai||{}, read=ai.key_readout||{}, alerts=d.alerts?.summary||{};
    if(tab==="overview") return `<div class="p4Grid">${card("Regime",read.regime||d.regime?.regime,"Score "+P.safe(read.regime_score||d.regime?.regime_score))}${card("News Impact",read.news_impact||d.regime?.news_impact||0)}${card("Top Rotation",(read.top_rotation||{}).move,""+((read.top_rotation||{}).action||""))}${card("Alerts",alerts.total||0,`${alerts.critical||0} critical · ${alerts.warning||0} warnings`)}</div><h2>What Should I Do?</h2><div class="p4Card">${list(ai.action_items)}</div><h2>Plain-English Summary</h2><div class="p4Card">${list(ai.plain_english_summary)}</div>`;
    if(tab==="ai") return render("overview")+newsTable(ai.top_news||[]);
    if(tab==="alerts"){let rows=d.alerts?.alerts||[]; return `<div class="p4Grid">${card("Critical",alerts.critical||0)}${card("Warnings",alerts.warning||0)}${card("Total",alerts.total||rows.length||0)}</div>${alertTable(rows)}`}
    if(tab==="market") return table((d.market?.trade_ready||d.market?.top_candidates||[]).slice(0,40),["symbol","final_score","score","entry_zone","label"]);
    if(tab==="overnight") return `<div class="p4Grid">${card("Market",d.overnight?.market_label)}${card("Risk",d.overnight?.risk_score)}${card("News Impact",d.overnight?.news_impact||0)}</div><div class="p4Card">${list(d.overnight?.notes)}</div>${newsTable(d.overnight?.news||[])}`;
    if(tab==="sell") return table((d.sell?.sell_candidates||[]).slice(0,40),["symbol","sell_pressure","verdict","reasons"]);
    if(tab==="rotation") return table((d.rotation?.rotation_suggestions||[]).slice(0,60),["sell_symbol","buy_symbol","action","rotation_score","confidence","regime"]);
    if(tab==="shadow") return `<pre class="p4Card">${P.esc(JSON.stringify(d.shadow,null,2))}</pre>`;
    if(tab==="performance") return `<pre class="p4Card">${P.esc(JSON.stringify(d.perf?.summary||d.perf,null,2))}</pre>`;
    if(tab==="learning") return `<div class="p4Grid">${card("XP",((d.perf?.summary?.evaluated||0)*5)+((d.achievements?.achievements||[]).length*25))}${card("Achievements",(d.achievements?.achievements||[]).length)}${card("Pending",d.perf?.summary?.pending_evaluations||0)}</div><div class="p4Card">${list(["Review AI Summary.","Check Alerts.","Let tracker collect outcomes.","Do not connect new systems to live trading yet.","Use Debug Snapshot before asking for help."])}</div>`;
    if(tab==="future") return `<div class="p4Grid">${["IPO Watch","Day Trading Lab","Crypto / ETF / Commodities","Social Trend Scanner","Event / News Impact Layer","Strategy Sandbox","Manual Testing Lab"].map(x=>`<div class="p4Card"><h3>${x}</h3><p class="p4Muted">Placeholder: research-only expansion slot.</p><span class="p4Badge p4Warn">future</span></div>`).join("")}</div>`;
    if(tab==="settings") return `<div class="p4Card"><h3>Simple Settings</h3><p>Full theme studio will be added after the layout is stable.</p><button class="p4Btn" id="p4ClearSeen">Reset popup history</button></div>`;
    if(tab==="debug") return `<div class="p4Card"><button class="p4Btn" id="p4CopyDebug">Copy Debug Snapshot</button><pre>${P.esc(snapshot())}</pre></div>`;
    return "";
  }

  function table(rows,keys){return `<table class="p4Table"><thead><tr>${keys.map(k=>`<th>${k}</th>`).join("")}</tr></thead><tbody>${rows.map(r=>`<tr>${keys.map(k=>`<td>${Array.isArray(r[k])?r[k].map(P.esc).join("<br>"):P.esc(P.safe(r[k],""))}</td>`).join("")}</tr>`).join("")||`<tr><td colspan="${keys.length}">No rows.</td></tr>`}</tbody></table>`}
  function newsTable(rows){return `<h2>News</h2><table class="p4Table"><tbody>${rows.slice(0,20).map(n=>`<tr><td><b>${P.esc(n.headline||n.title)}</b><br><span class="p4Muted">${P.esc(n.source)} · impact ${P.safe(n.impact_score)}</span></td></tr>`).join("")||"<tr><td>No news.</td></tr>"}</tbody></table>`}
  function alertTable(rows){return `<table class="p4Table"><thead><tr><th>Level</th><th>Category</th><th>Title</th><th>Message</th></tr></thead><tbody>${rows.map(a=>`<tr><td><span class="p4Badge ${a.level==="critical"?"p4Risk":a.level==="warning"?"p4Warn":"p4Good"}">${P.esc(a.level)}</span></td><td>${P.esc(a.category)}</td><td><b>${P.esc(a.title)}</b></td><td>${P.esc(a.message)}</td></tr>`).join("")||"<tr><td colspan=4>No alerts.</td></tr>"}</tbody></table>`}
  function snapshot(){return JSON.stringify({time:new Date().toISOString(),url:location.href,ai:P.data.ai?.key_readout,alerts:P.data.alerts?.summary,regime:P.data.regime,performance:P.data.perf?.summary},null,2)}
  function bindInside(tab){const c=document.getElementById("p4CopyDebug"); if(c)c.onclick=()=>P.copy(snapshot()); const r=document.getElementById("p4ClearSeen"); if(r)r.onclick=()=>{Object.keys(localStorage).filter(k=>k.startsWith("p4_seen_")).forEach(k=>localStorage.removeItem(k)); P.toast({title:"Reset",message:"Popup history cleared."})}}

  async function mood(){
    try{const a=await P.json("/static/research/notifications_latest.json"); const s=a.summary||{}; const b=document.getElementById("p4AssistantBtn"); if((s.critical||0)>0)b.innerHTML="🛡️"; else if((s.warning||0)>0)b.innerHTML="⚠️"; else b.innerHTML="🐕"; (a.alerts||[]).filter(x=>["critical","warning"].includes(x.level)).slice(0,2).forEach(x=>P.toast(x));}catch(e){}
  }

  shell(); mood(); setInterval(mood,60000);
})();
''')

wd=Path("web_dashboard.py")
text=wd.read_text()
Path("web_dashboard.py.bak_before_ponder_site_v4").write_text(text)

text=re.sub(r'\n# === PONDER_MODULAR_UI_V2 ===.*?# === END_PONDER_MODULAR_UI_V2 ===\n','\n',text,flags=re.S)
text=re.sub(r'\n# === PONDER_MODULAR_UI_V3 ===.*?# === END_PONDER_MODULAR_UI_V3 ===\n','\n',text,flags=re.S)
text=re.sub(r'\n# === PONDER_SITE_V4 ===.*?# === END_PONDER_SITE_V4 ===\n','\n',text,flags=re.S)
text=re.sub(r'\n?\s*<script src="/static/ponder_ui\.js\?v=[^"]+"></script>','',text)
text=re.sub(r'\n?\s*<script src="/static/ponder3/[^"]+"></script>','',text)
text=re.sub(r'\n?\s*<link rel="stylesheet" href="/static/ponder3/[^"]+">','',text)

loader=f'''
# === PONDER_SITE_V4 ===
@app.after_request
def ponder_site_v4(response):
    try:
        if request.path.startswith("/login"):
            return response
        ctype = response.headers.get("Content-Type", "")
        if "text/html" not in ctype:
            return response
        html = response.get_data(as_text=True)
        if "/static/ponder4/app.js" in html:
            return response
        assets = """
<link rel="stylesheet" href="/static/ponder4/theme.css?v={VERSION}">
<script src="/static/ponder4/app.js?v={VERSION}"></script>
"""
        if "</body>" in html:
            html = html.replace("</body>", assets + "\\n</body>")
        else:
            html += assets
        response.set_data(html)
    except Exception:
        pass
    return response
# === END_PONDER_SITE_V4 ===
'''
marker='if __name__ == "__main__":'
text=text.replace(marker,loader+"\n"+marker) if marker in text else text+"\n"+loader
wd.write_text(text)

Path("rollback_ponder_site_v4.sh").write_text("""#!/bin/bash
cd /home/ubuntu/trading-bot || exit 1
cp web_dashboard.py.bak_before_ponder_site_v4 web_dashboard.py
sudo systemctl restart tradebot-dashboard.service
echo "Rolled back Ponder Site v4."
""")
print("✅ Ponder Site v4 installed")
print("Rollback: bash rollback_ponder_site_v4.sh")
