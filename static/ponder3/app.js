
(function(){
  if(window.__PonderV3App) return;
  window.__PonderV3App = true;

  if(location.pathname === "/login" || location.pathname.startsWith("/login")) return;

  const P = {
    version:"ponderv3clean1",
    state:{active:"overview", data:{}, settings:{}},
    sources:{
      market:"/static/research/market_intelligence_latest.json",
      overnight:"/static/research/overnight_brief_latest.json",
      sell:"/static/research/sell_intelligence_latest.json",
      rotation:"/static/research/rotation_engine_latest.json",
      performance:"/static/research/rotation_performance_latest.json",
      shadow:"/static/research/shadow_capital_allocator_latest.json",
      regime:"/static/research/market_regime_filter_latest.json",
      ai:"/static/research/ai_summary_latest.json",
      alerts:"/static/research/notifications_latest.json",
      assistant:"/static/research/ponder_assistant_latest.json",
      achievements:"/static/research/achievements_latest.json"
    },
    future:[
      ["ipo","IPO Watch","Research-only IPO watchlist placeholder."],
      ["daytrade","Day Trading Lab","Fast-market setup research placeholder."],
      ["crypto","Crypto / ETF / Commodities","Separate-market scanner placeholder."],
      ["social","Social Trend Scanner","TikTok/social catalyst research placeholder."],
      ["events","Event / News Impact Layer","Reserved for advanced event tagging."],
      ["strategy","Strategy Sandbox","Paper-only strategy experiment area."]
    ],
    safe(v,f="—"){return (v===undefined||v===null||v===""||Number.isNaN(v))?f:v},
    esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))},
    async json(path){
      const r = await fetch(path+"?ts="+Date.now(),{cache:"no-store"});
      if(!r.ok) throw new Error(path);
      return await r.json();
    },
    loadSettings(){
      try{this.state.settings = JSON.parse(localStorage.getItem("ponderV3Settings")||"{}")}catch(e){this.state.settings={}}
      this.applySettings();
    },
    saveSettings(){
      localStorage.setItem("ponderV3Settings",JSON.stringify(this.state.settings));
      this.applySettings();
    },
    applySettings(){
      document.body.classList.toggle("ponder-v3-active",true);
      document.body.classList.toggle("ponder-colorblind", this.state.settings.colorblind !== false);
      document.body.classList.toggle("ponder-adhd", !!this.state.settings.adhd);
      document.body.classList.toggle("ponder-bigclick", this.state.settings.bigclick !== false);
      document.body.classList.toggle("ponder-compact", !!this.state.settings.compact);
    },
    say(msg,seconds=7){
      let b=document.getElementById("ponderV3Speech");
      if(!b){b=document.createElement("div");b.id="ponderV3Speech";document.body.appendChild(b)}
      b.innerHTML="🐕 "+this.esc(msg);
      b.style.display="block";
      clearTimeout(window.__ponderV3SpeechTimer);
      window.__ponderV3SpeechTimer=setTimeout(()=>b.style.display="none",seconds*1000);
    },
    copy(text){
      navigator.clipboard?.writeText(text);
      this.say("Copied. Send that snapshot when you need help.");
    }
  };
  window.PonderV3 = P;

  async function loadAll(){
    const entries = Object.entries(P.sources);
    const settled = await Promise.allSettled(entries.map(([_,path])=>P.json(path)));
    entries.forEach(([k],i)=>P.state.data[k]=settled[i].status==="fulfilled"?settled[i].value:{});
    return P.state.data;
  }

  function card(title,value,note=""){
    return `<div class="ponderV3Card"><h3>${title}</h3><div class="ponderV3Big">${P.safe(value)}</div><div class="ponderV3Muted">${note}</div></div>`;
  }
  function list(items){return `<ul>${(items||[]).map(x=>`<li>${P.esc(x)}</li>`).join("")||"<li>No data yet.</li>"}</ul>`}
  function stale(updated){
    if(!updated) return `<span class="ponderV3Badge yellow">No timestamp</span>`;
    const dt = new Date(String(updated).replace(" ","T")+"Z");
    if(isNaN(dt)) return `<span class="ponderV3Badge yellow">Unknown freshness</span>`;
    const mins = Math.round((Date.now()-dt.getTime())/60000);
    if(mins > 180) return `<span class="ponderV3Badge red">Stale ${mins}m</span>`;
    return `<span class="ponderV3Badge">Fresh ${mins}m</span>`;
  }

  function makeShell(){
    if(document.getElementById("ponderV3Sidebar")) return;
    const side=document.createElement("aside");
    side.id="ponderV3Sidebar";
    side.innerHTML=`
      <div>
        <div class="ponderV3Brand">🐾 Ponder<span>AI</span></div>
        <div class="ponderV3Sub">Professional research-only command center. No live orders from this UI.</div>
      </div>
      <div class="ponderV3NavGroup">
        <div class="ponderV3NavTitle">Dashboard</div>
        <button class="ponderV3NavBtn" data-page-link="/">🏠 Main</button>
        <button class="ponderV3NavBtn" data-page-link="/profit">📈 Profit Ops</button>
        <button class="ponderV3NavBtn" data-page-link="/profit-lab">🧪 Profit Lab</button>
        <button class="ponderV3NavBtn" data-page-link="/history">📜 History</button>
      </div>
      <div class="ponderV3NavGroup">
        <div class="ponderV3NavTitle">Command Center</div>
        <button class="ponderV3NavBtn" data-tab="overview">🧠 Overview</button>
        <button class="ponderV3NavBtn" data-tab="ai">🤖 AI Summary</button>
        <button class="ponderV3NavBtn" data-tab="assistant">🐕 Ask Ponder</button>
        <button class="ponderV3NavBtn" data-tab="alerts">🔔 Alerts</button>
        <button class="ponderV3NavBtn" data-tab="learning">🎮 Learning</button>
        <button class="ponderV3NavBtn" data-tab="settings">⚙️ Settings</button>
      </div>
      <div class="ponderV3SidebarBottom">
        <button class="ponderV3SmallBtn" id="ponderV3Refresh">Refresh Data</button>
        <button class="ponderV3SmallBtn" id="ponderV3Snapshot" style="margin-top:8px">Copy Snapshot</button>
        <div style="margin-top:10px">Ponder modes: Guard / Alert / Hunt / Idle</div>
      </div>
    `;
    document.body.appendChild(side);

    const main=document.createElement("main");
    main.id="ponderV3Main";
    document.body.appendChild(main);

    side.querySelectorAll("[data-page-link]").forEach(b=>b.onclick=()=>location.href=b.dataset.pageLink);
    side.querySelectorAll("[data-tab]").forEach(b=>b.onclick=()=>openTab(b.dataset.tab));
    document.getElementById("ponderV3Refresh").onclick=()=>openTab(P.state.active,true);
    document.getElementById("ponderV3Snapshot").onclick=()=>copySnapshot();
  }

  const render = {
    overview(d){
      const ai=d.ai||{}, read=ai.key_readout||{}, alerts=d.alerts.summary||{}, rot=d.rotation.top_rotation||{};
      return `
        <div class="ponderV3Grid">
          ${card("Regime", read.regime||d.regime.regime, "Score: "+P.safe(read.regime_score||d.regime.regime_score))}
          ${card("News Impact", read.news_impact||d.regime.news_impact||0, "High = more defensive")}
          ${card("Top Rotation", (read.top_rotation||{}).move || `${P.safe(rot.sell_symbol)} → ${P.safe(rot.buy_symbol)}`, (read.top_rotation||{}).action || rot.action || "")}
          ${card("Alerts", alerts.total||0, `${alerts.critical||0} critical · ${alerts.warning||0} warnings`)}
        </div>
        <h2>🧭 What Should I Do?</h2><div class="ponderV3Card" style="border-color:var(--p-green)">${list(ai.action_items)}</div>
        <h2>Plain-English Summary</h2><div class="ponderV3Card">${list(ai.plain_english_summary)}</div>
        <h2>Active Modules</h2>
        <div class="ponderV3Grid">
          ${Object.entries(P.sources).map(([k])=>`<div class="ponderV3Card"><h3>${k}</h3>${stale((d[k]||{}).updated_at)}</div>`).join("")}
        </div>`;
    },
    ai(d){
      const ai=d.ai||{}, r=ai.key_readout||{}, news=ai.top_news||[];
      return `
        <div class="ponderV3Grid">
          ${card("Regime", r.regime, "Score: "+P.safe(r.regime_score))}
          ${card("Top Rotation", (r.top_rotation||{}).move, `${(r.top_rotation||{}).action||""} · ${(r.top_rotation||{}).confidence||""}`)}
          ${card("Pending Learning", r.pending_evaluations, "rotation outcomes")}
        </div>
        <h2>What Should I Do?</h2><div class="ponderV3Card">${list(ai.action_items)}</div>
        <h2>Simple Explanation</h2><div class="ponderV3Card">${list(ai.plain_english_summary)}</div>
        <h2>News Drivers</h2><table class="ponderV3Table"><thead><tr><th>Headline</th><th>Source</th><th>Impact</th><th>Tags</th></tr></thead><tbody>
        ${news.map(n=>`<tr><td><strong>${P.esc(n.headline)}</strong></td><td>${P.esc(n.source)}</td><td>${P.safe(n.impact_score)}</td><td>${(n.tags||[]).join(", ")}</td></tr>`).join("")||`<tr><td colspan="4">No news drivers.</td></tr>`}
        </tbody></table>`;
    },
    assistant(d){
      const a=d.assistant||{}, ans=a.answers||{};
      const qs=[["why_no_trade","Why didn’t you trade?"],["biggest_risk","Biggest risk?"],["should_rotate","Should I rotate?"],["what_to_do","What should I do?"],["plain_english","Explain simply"],["changed","What changed since last time?"]];
      return `
        <div class="ponderV3Grid">
          ${card("Ponder Mode", (a.overseer||{}).market_regime||d.regime.regime, "Companion / overseer")}
          ${card("News Impact", (a.overseer||{}).news_impact||d.regime.news_impact||0)}
          ${card("Learning Pending", ((a.overseer||{}).learning||{}).pending || (d.performance.summary||{}).pending_evaluations || 0)}
        </div>
        <div class="ponderV3Card">${qs.map(([k,label])=>`<button class="ponderV3ActionBtn" data-answer="${k}">${label}</button>`).join("")}</div>
        <div class="ponderV3Card" id="ponderV3Answer">Click a question. Ponder will answer using current research data.</div>`;
    },
    alerts(d){
      const n=d.alerts||{}, s=n.summary||{}, rows=n.alerts||[];
      return `
        <div class="ponderV3Grid">${card("Critical",s.critical||0)}${card("Warnings",s.warning||0)}${card("Achievements",s.achievement||0)}${card("Total",s.total||rows.length||0)}</div>
        <div class="ponderV3Card"><button class="ponderV3ActionBtn" data-filter-alert="all">All</button><button class="ponderV3ActionBtn" data-filter-alert="critical">Critical</button><button class="ponderV3ActionBtn" data-filter-alert="warning">Warnings</button></div>
        <table class="ponderV3Table"><thead><tr><th>Level</th><th>Category</th><th>Title</th><th>Message</th></tr></thead><tbody id="ponderV3AlertsBody">
        ${rows.map(a=>alertRow(a)).join("")||`<tr><td colspan="4">No alerts.</td></tr>`}
        </tbody></table>`;
    },
    market(d){
      const rows=d.market.trade_ready||d.market.top_candidates||[];
      return `<h2>Market Scanner</h2><table class="ponderV3Table"><thead><tr><th>Symbol</th><th>Score</th><th>Entry</th><th>Label</th></tr></thead><tbody>
      ${rows.slice(0,40).map(x=>`<tr><td><strong>${P.esc(x.symbol)}</strong></td><td>${P.safe(x.final_score||x.score)}</td><td>${P.esc(x.entry_zone||"")}</td><td>${P.esc(x.label||"")}</td></tr>`).join("")||`<tr><td colspan="4">No scanner rows.</td></tr>`}
      </tbody></table>`;
    },
    overnight(d){
      const o=d.overnight||{};
      return `<div class="ponderV3Grid">${card("Market Label",o.market_label)}${card("Risk Score",o.risk_score)}${card("News Impact",o.news_impact||0)}</div>
      <h2>Notes</h2><div class="ponderV3Card">${list(o.notes)}</div>
      <h2>News</h2><table class="ponderV3Table"><tbody>${(o.news||[]).slice(0,20).map(n=>`<tr><td><strong>${P.esc(n.headline)}</strong><br><span class="ponderV3Muted">${P.esc(n.source)} · impact ${P.safe(n.impact_score)}</span></td></tr>`).join("")||`<tr><td>No news rows.</td></tr>`}</tbody></table>`;
    },
    sell(d){
      const rows=d.sell.sell_candidates||[];
      return `<h2>Sell Intelligence</h2><table class="ponderV3Table"><thead><tr><th>Symbol</th><th>Pressure</th><th>Verdict</th><th>Reasons</th></tr></thead><tbody>
      ${rows.slice(0,40).map(x=>`<tr><td><strong>${P.esc(x.symbol)}</strong></td><td>${P.safe(x.sell_pressure)}</td><td>${P.esc(x.verdict)}</td><td>${(x.reasons||[]).map(P.esc).join("<br>")}</td></tr>`).join("")||`<tr><td colspan="4">No sell rows.</td></tr>`}
      </tbody></table>`;
    },
    rotation(d){
      const rows=d.rotation.rotation_suggestions||[];
      return `<div class="ponderV3Grid">${card("Version",d.rotation.version)}${card("Found",(d.rotation.summary||{}).rotations_found||rows.length)}${card("Rotate Now",(d.rotation.summary||{}).rotate_now_count||0)}</div>
      <table class="ponderV3Table"><thead><tr><th>Move</th><th>Action</th><th>Score</th><th>Regime</th><th>Why</th></tr></thead><tbody>
      ${rows.slice(0,50).map(x=>`<tr><td><strong>${P.esc(x.sell_symbol)} → ${P.esc(x.buy_symbol)}</strong></td><td>${P.esc(x.action)}</td><td>${P.safe(x.rotation_score)}</td><td>${P.esc(x.regime||"")}</td><td>${(x.why||[]).map(P.esc).join("<br>")}</td></tr>`).join("")||`<tr><td colspan="5">No rotations.</td></tr>`}
      </tbody></table>`;
    },
    performance(d){
      const s=d.performance.summary||{}, h=d.performance.by_horizon||{};
      return `<div class="ponderV3Grid">${card("Win Rate",(s.win_rate||0)+"%",s.primary_horizon||"60m")}${card("Evaluated",s.evaluated||0)}${card("Pending",s.pending_evaluations||0)}${card("Avg Alpha",(s.avg_alpha_pct||0)+"%")}</div>
      <div class="ponderV3Card"><h3>Horizon Snapshot</h3><pre>${P.esc(JSON.stringify(h,null,2))}</pre></div>`;
    },
    learning(d){
      const a=d.achievements||{}, rows=a.achievements||[];
      const perf=d.performance.summary||{};
      return `<div class="ponderV3Grid">${card("XP",calcXP(d), "research learning points")}${card("Achievements",a.total_unlocked||rows.length||0)}${card("Signals Pending",perf.pending_evaluations||0)}${card("Evaluated",perf.evaluated||0)}</div>
      <h2>Daily Missions</h2><div class="ponderV3Card">${list(dailyMissions(d))}</div>
      <h2>Achievements</h2><div class="ponderV3Grid">${rows.map(x=>`<div class="ponderV3Card"><h3>${P.esc(x.title)}</h3><p>${P.esc(x.description)}</p></div>`).join("")||`<div class="ponderV3Card">No achievements yet.</div>`}</div>`;
    },
    future(d){
      return `<h2>Future Research Labs</h2><div class="ponderV3Grid">${P.future.map(([id,title,desc])=>`<div class="ponderV3Card"><h3>${title}</h3><p>${desc}</p><span class="ponderV3Badge yellow">Placeholder</span></div>`).join("")}</div>`;
    },
    settings(d){
      const s=P.state.settings;
      return `<h2>Settings</h2><div class="ponderV3Card">
        ${settingRow("Colorblind Mode","colorblind",s.colorblind!==false)}
        ${settingRow("ADHD / Simple Mode","adhd",!!s.adhd)}
        ${settingRow("Big Click Mode","bigclick",s.bigclick!==false)}
        ${settingRow("Compact Mode","compact",!!s.compact)}
        ${settingRow("Toast Alerts","toasts",s.toasts!==false)}
      </div>`;
    },
    debug(d){
      const snap=makeSnapshot();
      return `<div class="ponderV3Card"><button class="ponderV3ActionBtn" id="ponderCopySnap">Copy Debug Snapshot</button><pre>${P.esc(snap)}</pre></div>`;
    }
  };

  function alertRow(a){
    const cls=a.level==="critical"?"red":a.level==="warning"?"yellow":"";
    return `<tr data-alert-level="${P.esc(a.level)}"><td><span class="ponderV3Badge ${cls}">${P.esc(a.level)}</span></td><td>${P.esc(a.category)}</td><td><strong>${P.esc(a.title)}</strong></td><td>${P.esc(a.message)}</td></tr>`;
  }

  function settingRow(label,key,on){
    return `<div class="ponderV3SettingsRow"><div><strong>${label}</strong><div class="ponderV3Muted">Persistent setting</div></div><button class="ponderV3ActionBtn" data-setting="${key}">${on?"ON":"OFF"}</button></div>`;
  }
  function calcXP(d){return ((d.performance.summary||{}).evaluated||0)*5 + ((d.achievements.achievements||[]).length*25) + ((d.alerts.summary||{}).total||0)*2}
  function dailyMissions(d){
    return [
      "Review AI Summary before making changes.",
      "Check Alerts for regime/news risk.",
      "Let rotation tracker collect more outcomes.",
      "Do not connect new systems to live trading yet.",
      "Use Debug Snapshot before asking for help."
    ];
  }
  function makeSnapshot(){
    const d=P.state.data;
    return JSON.stringify({time:new Date().toISOString(),url:location.href,version:P.version,ai:d.ai?.key_readout,alerts:d.alerts?.summary,regime:d.regime,rotation:d.rotation?.top_rotation,performance:d.performance?.summary},null,2);
  }
  function copySnapshot(){P.copy(makeSnapshot())}

  async function openTab(tab="overview", force=false){
    P.state.active=tab;
    makeShell();
    const main=document.getElementById("ponderV3Main");
    main.classList.add("open");
    main.innerHTML=`<div class="ponderV3Topbar"><div><h1 class="ponderV3Title">🐾 PonderAI Command Center</h1><div class="ponderV3Muted">Loading ${P.esc(tab)}...</div></div><button class="ponderV3Close" id="ponderV3Close">Close</button></div><div class="ponderV3Content">Loading...</div>`;
    document.getElementById("ponderV3Close").onclick=()=>main.classList.remove("open");
    await loadAll();
    const content=render[tab]?render[tab](P.state.data):render.overview(P.state.data);
    main.innerHTML=`<div class="ponderV3Topbar"><div><h1 class="ponderV3Title">🐾 PonderAI Command Center</h1><div class="ponderV3Muted">Research-only · refreshed ${new Date().toLocaleTimeString()}</div></div><div><button class="ponderV3SmallBtn" id="ponderV3ManualRefresh">Refresh</button> <button class="ponderV3Close" id="ponderV3Close">Close</button></div></div><div class="ponderV3Content">${content}</div>`;
    document.getElementById("ponderV3Close").onclick=()=>main.classList.remove("open");
    document.getElementById("ponderV3ManualRefresh").onclick=()=>openTab(tab,true);
    bindDynamic();
    document.querySelectorAll(".ponderV3NavBtn").forEach(b=>b.classList.toggle("active",b.dataset.tab===tab));
  }

  function bindDynamic(){
    document.querySelectorAll("[data-answer]").forEach(btn=>btn.onclick=()=>{
      const d=P.state.data, ans=(d.assistant||{}).answers||{}, key=btn.dataset.answer;
      let items=ans[key]||[];
      if(key==="changed") items=["Compare the latest Debug Snapshot with an older one to see changes. Full change tracking will be added later."];
      document.getElementById("ponderV3Answer").innerHTML=`<ul>${items.map(x=>`<li>${P.esc(x)}</li>`).join("")||"<li>No answer yet.</li>"}</ul>`;
      P.say("I answered using the latest research data.");
    });
    document.querySelectorAll("[data-filter-alert]").forEach(btn=>btn.onclick=()=>{
      const level=btn.dataset.filterAlert;
      document.querySelectorAll("[data-alert-level]").forEach(row=>row.style.display=(level==="all"||row.dataset.alertLevel===level)?"":"none");
    });
    document.querySelectorAll("[data-setting]").forEach(btn=>btn.onclick=()=>{
      const key=btn.dataset.setting;
      const map={colorblind:"colorblind",adhd:"adhd",bigclick:"bigclick",compact:"compact",toasts:"toasts"};
      P.state.settings[map[key]]=!(P.state.settings[map[key]]!==false && !["adhd","compact"].includes(key) || !!P.state.settings[map[key]]);
      if(["adhd","compact"].includes(key)) P.state.settings[map[key]]=!P.state.settings[map[key]];
      P.saveSettings();
      openTab("settings",true);
    });
    const snap=document.getElementById("ponderCopySnap");
    if(snap) snap.onclick=copySnapshot;
  }

  function makePup(){
    if(document.getElementById("ponderV3Pup")) return;
    const b=document.createElement("button");
    b.id="ponderV3Pup";
    b.innerHTML="🐕";
    b.title="Ask Ponder";
    b.onclick=()=>openTab("assistant");
    document.body.appendChild(b);
  }

  async function updateMood(){
    makePup();
    try{
      const data=await P.json("/static/research/notifications_latest.json");
      const s=data.summary||{};
      const b=document.getElementById("ponderV3Pup");
      let icon="😴🐕", cls="idle", msg="Ponder is resting. No major alerts.";
      if((s.critical||0)>0){icon="🛡️🐕";cls="guard";msg="Guard Mode: critical risk is active."}
      else if((s.warning||0)>0){icon="⚠️🐕";cls="alert";msg="Alert Mode: Ponder smells risk."}
      else if((s.total||0)>0){icon="🐕";cls="hunt";msg="Watch Mode: Ponder is monitoring opportunities."}
      b.innerHTML=icon;b.className=cls;b.title=cls.toUpperCase();
      if(b.dataset.mode!==cls){b.dataset.mode=cls;P.say(msg)}
    }catch(e){}
  }

  function toast(a){
    if(P.state.settings.toasts===false) return;
    const key="ponder_v3_seen_"+(a.key||a.level+"::"+a.title+"::"+a.message);
    if(localStorage.getItem(key)) return;
    localStorage.setItem(key,"1");
    let w=document.getElementById("ponderV3ToastWrap");
    if(!w){w=document.createElement("div");w.id="ponderV3ToastWrap";document.body.appendChild(w)}
    const el=document.createElement("div");
    el.className="ponderV3Toast "+(a.level||"");
    el.innerHTML=`<div style="font-weight:950;margin-bottom:4px">🐕 ${P.esc(a.title)}</div><div>${P.esc(a.message)}</div>`;
    w.appendChild(el);
    setTimeout(()=>el.remove(),a.level==="critical"?10000:7000);
  }
  async function pollAlerts(){
    try{const d=await P.json("/static/research/notifications_latest.json");(d.alerts||[]).filter(a=>["critical","warning"].includes(a.level)).slice(0,3).forEach(toast)}catch(e){}
  }

  function boot(){
    P.loadSettings();
    makeShell();
    makePup();
    updateMood();
    pollAlerts();
    setInterval(updateMood,45000);
    setInterval(pollAlerts,60000);
  }

  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",boot); else boot();
})();
