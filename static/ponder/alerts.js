
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
