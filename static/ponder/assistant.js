
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
