
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
